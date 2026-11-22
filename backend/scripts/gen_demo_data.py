"""產生 db/init/04_demo_data.sql：示範用的交易資料（訂單、明細、折扣、狀態歷程、退貨、評價、購物車）。

做法：在一個暫存資料庫上用後端真正的服務（services/orders.py、services/pricing.py）跑一遍情境，
金額因此一定符合 BR-09～BR-12、退款符合 BR-26；同時把每一步寫成 SQL。
產生的 SQL 依照業務流程的順序執行（先建立 received 訂單，再逐步 UPDATE 狀態、申請與審核退貨），
所以會經過 02_triggers.sql 所有 trigger 的檢查，狀態歷程也是由 trigger 自動產生。

執行（需要 docker compose 的 db 在 localhost:5433）：
    cd backend && .venv/bin/python scripts/gen_demo_data.py
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = "fuwa_demo_gen"
os.environ["DATABASE_URL"] = f"postgresql+psycopg://fuwa:fuwa@localhost:5433/{SCRATCH}"
sys.path.insert(0, str(ROOT / "backend"))

INIT = [ROOT / "db" / "init" / f for f in ("01_schema.sql", "02_triggers.sql", "03_seed.sql")]
OUT = ROOT / "db" / "init" / "04_demo_data.sql"

with psycopg.connect("postgresql://fuwa:fuwa@localhost:5433/postgres", autocommit=True) as c:
    c.execute(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)")
    c.execute(f"CREATE DATABASE {SCRATCH}")
with psycopg.connect(f"postgresql://fuwa:fuwa@localhost:5433/{SCRATCH}", autocommit=True) as c:
    c.execute("\n".join(p.read_text() for p in INIT))

from app.db import SessionLocal  # noqa: E402
from app.models import CartItem, Order, StoreReview, User  # noqa: E402
from app.services import orders as svc  # noqa: E402

db = SessionLocal()
sql: list[str] = []
STAFF = 2


def lit(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, Decimal)):
        return str(int(v))
    if isinstance(v, datetime):
        return f"'{v:%Y-%m-%d %H:%M:%S}'"
    return "'" + str(v).replace("'", "''") + "'"


def actor(uid: int) -> None:
    sql.append(f"SELECT set_config('app.user_id', '{uid}', false);")


def stamp_history(order_id: int, t: datetime) -> None:
    sql.append(f"UPDATE order_status_history SET changed_at = {lit(t)} WHERE order_id = {order_id} "
               f"AND seq_no = (SELECT MAX(seq_no) FROM order_status_history WHERE order_id = {order_id});")


def place(user_id: int, items: list[tuple[int, int]], t: datetime, note: str) -> Order:
    user = db.get(User, user_id)
    for pid, qty in items:
        db.add(CartItem(user_id=user_id, product_id=pid, quantity=qty))
    db.flush()
    o = svc.checkout(db, user, user.name, user.phone, user.address, order_time=t)
    db.commit()
    sql.append(f"\n-- 訂單 #{o.order_id}：{note}")
    sql.append(
        "INSERT INTO orders (order_id, user_id, order_time, recipient_name, recipient_phone, recipient_address, "
        "subtotal, discount_total, tax, shipping_fee, total, status, paid_at) VALUES ("
        + ", ".join(lit(v) for v in (o.order_id, o.user_id, o.order_time, o.recipient_name, o.recipient_phone,
                                    o.recipient_address, o.subtotal, o.discount_total, o.tax, o.shipping_fee,
                                    o.total, "received", o.paid_at)) + ");")
    sql.append("INSERT INTO order_item (order_id, item_no, product_id, product_name, unit_price, quantity, event_discount) VALUES\n    "
               + ",\n    ".join("(" + ", ".join(lit(v) for v in (o.order_id, it.item_no, it.product_id, it.product_name,
                                                                  it.unit_price, it.quantity, it.event_discount)) + ")"
                               for it in o.items) + ";")
    if o.discounts:
        sql.append("INSERT INTO order_discount (order_id, discount_code, amount) VALUES\n    "
                   + ",\n    ".join(f"({o.order_id}, {lit(d.discount_code)}, {lit(d.amount)})" for d in o.discounts) + ";")
    for it in o.items:  # BR-06：付款後扣庫存
        sql.append(f"UPDATE product SET stock = stock - {it.quantity} WHERE product_id = {it.product_id};")
    return o


def advance(o: Order, *statuses_and_times: tuple[str, datetime]) -> None:
    for status, t in statuses_and_times:
        svc.advance_status(db, o, db.get(User, STAFF), status)
        db.commit()
        actor(STAFF)
        sql.append(f"UPDATE orders SET status = '{status}' WHERE order_id = {o.order_id};")
        stamp_history(o.order_id, t)


def cancel(o: Order, t: datetime) -> None:
    svc.cancel_order(db, o, db.get(User, o.user_id))
    db.commit()
    actor(o.user_id)
    sql.append(f"UPDATE orders SET status = 'cancelled' WHERE order_id = {o.order_id};")
    stamp_history(o.order_id, t)
    for it in o.items:  # 取消後回補庫存
        sql.append(f"UPDATE product SET stock = stock + {it.quantity} WHERE product_id = {it.product_id};")


def request_return(o: Order, items: list[tuple[int, int]], reason: str, t: datetime):
    rr = svc.create_return(db, o, reason, items)
    db.commit()
    sql.append(f"INSERT INTO return_request (return_id, order_id, requested_at, reason) VALUES "
               f"({rr.return_id}, {o.order_id}, {lit(t)}, {lit(reason)});")
    sql.append("INSERT INTO return_item (return_id, order_id, item_no, return_qty) VALUES "
               + ", ".join(f"({rr.return_id}, {o.order_id}, {no}, {q})" for no, q in items) + ";")
    return rr


def approve(o: Order, rr, t: datetime) -> None:
    svc.approve_return(db, rr, db.get(User, STAFF))
    db.commit()
    db.refresh(o)
    sql.append(f"UPDATE return_request SET status = 'approved', processed_by = {STAFF}, processed_at = {lit(t)}, "
               f"refund_total = {lit(rr.refund_total)} WHERE return_id = {rr.return_id};")
    by_no = {it.item_no: it for it in o.items}
    for ri in rr.items:
        sql.append(f"UPDATE return_item SET refund_amount = {lit(ri.refund_amount)} "
                   f"WHERE return_id = {rr.return_id} AND item_no = {ri.item_no};")
        sql.append(f"UPDATE product SET stock = stock + {ri.return_qty} WHERE product_id = {by_no[ri.item_no].product_id};")
    if o.status == "returned":  # 所有商品都退貨才改為 returned（BR-19）
        actor(STAFF)
        sql.append(f"UPDATE orders SET status = 'returned' WHERE order_id = {o.order_id};")
        stamp_history(o.order_id, t)


def reject(rr, reason: str, t: datetime) -> None:
    svc.reject_return(db, rr, db.get(User, STAFF), reason)
    db.commit()
    sql.append(f"UPDATE return_request SET status = 'rejected', processed_by = {STAFF}, processed_at = {lit(t)}, "
               f"reject_reason = {lit(reason)} WHERE return_id = {rr.return_id};")


def review(o: Order, store_id: int, rating: int, comment: str, t: datetime) -> None:
    db.add(StoreReview(order_id=o.order_id, store_id=store_id, rating=rating, comment=comment, reviewed_at=t))
    db.commit()
    sql.append(f"INSERT INTO store_review (order_id, store_id, rating, comment, reviewed_at) VALUES "
               f"({o.order_id}, {store_id}, {rating}, {lit(comment)}, {lit(t)});")


def T(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def d(t: datetime, days: float) -> datetime:
    return t + timedelta(days=days)


ALICE, BOB = 4, 5

# ---------------- 情境 ----------------
t = T("2026-09-05 10:12")
o1 = place(ALICE, [(1, 2), (6, 1)], t, "alice 跨店（信義＋左營），未達免運，已完成")
advance(o1, ("processing", d(t, .2)), ("shipping", d(t, 1)), ("closed", d(t, 3)))
review(o1, 1, 5, "啾啾球超耐咬，狗狗玩了一整天！", d(t, 4))
review(o1, 3, 4, "項圈質感很好，出貨稍慢。", d(t, 4))

t = T("2026-09-12 14:30")
o2 = place(BOB, [(3, 1), (8, 3)], t, "bob 台中店，已完成")
advance(o2, ("processing", d(t, .3)), ("shipping", d(t, 1)), ("closed", d(t, 2.5)))
review(o2, 2, 4, "凍乾零食貓咪很愛，梳子也好用。", d(t, 3))

t = T("2026-09-20 20:05")
o3 = place(ALICE, [(4, 1)], t, "alice 買寵物籠，滿 1000 免運，已完成")
advance(o3, ("processing", d(t, .5)), ("shipping", d(t, 1.5)), ("closed", d(t, 4)))

t = T("2026-10-03 09:40")
o4 = place(BOB, [(5, 6), (13, 2)], t, "bob 信義店，已完成")
advance(o4, ("processing", d(t, .2)), ("shipping", d(t, 1)), ("closed", d(t, 2)))
review(o4, 1, 3, "逗貓棒羽毛有點容易掉。", d(t, 3))

t = T("2026-10-10 16:20")
o5 = place(ALICE, [(10, 1), (12, 2)], t, "alice 左營店，已完成後部分退貨（已核准）")
advance(o5, ("processing", d(t, .2)), ("shipping", d(t, 1)), ("closed", d(t, 2)))
rr5 = request_return(o5, [(2, 1)], "洗毛精多買了一瓶，未拆封。", d(t, 4))
approve(o5, rr5, d(t, 5))

t = T("2026-10-18 11:00")
o6 = place(BOB, [(11, 1)], t, "bob 下單後取消")
cancel(o6, d(t, .1))

t = T("2026-10-25 13:15")
o7 = place(ALICE, [(2, 2), (7, 1)], t, "alice 處理中全部退貨（核准後訂單改為 returned，運費一併退還）")
advance(o7, ("processing", d(t, .3)))
rr7 = request_return(o7, [(1, 2), (2, 1)], "尺寸不合，全部退貨。", d(t, .5))
approve(o7, rr7, d(t, 1))

t = T("2026-10-28 19:45")
o8 = place(ALICE, [(12, 1)], t, "alice 已完成，退貨申請被拒絕")
advance(o8, ("processing", d(t, .2)), ("shipping", d(t, 1)), ("closed", d(t, 2)))
rr8 = request_return(o8, [(1, 1)], "不喜歡味道。", d(t, 9))
reject(rr8, "商品已開封使用，不符合退貨條件。", d(t, 10))

t = T("2026-11-05 08:50")
o9 = place(BOB, [(9, 1), (5, 3)], t, "bob 貓跳台 8 折＋主食罐買 2 送 1＋冬季 95 折，配送中")
advance(o9, ("processing", d(t, .2)), ("shipping", d(t, 1)))

t = T("2026-11-12 21:10")
o10 = place(ALICE, [(14, 1), (8, 2)], t, "alice 季節折扣疊加，配送中，有待審核的退貨申請")
advance(o10, ("processing", d(t, .4)), ("shipping", d(t, 1.2)))
request_return(o10, [(2, 1)], "零食包裝破損。", d(t, 3))

t = T("2026-11-18 10:30")
o11 = place(BOB, [(1, 1), (3, 1), (6, 1)], t, "bob 三店各一件，處理中")
advance(o11, ("processing", d(t, .5)))

t = T("2026-11-20 15:00")
place(ALICE, [(9, 1), (5, 3)], t, "alice 新訂單，已接單")

t = T("2026-11-21 22:40")
place(BOB, [(13, 3)], t, "bob 新訂單，已接單")

# 購物車
sql.append("\n-- 購物車（DR-04）")
for uid, pid, qty, at in [(ALICE, 10, 1, "2026-11-21 23:00"), (ALICE, 13, 2, "2026-11-21 23:02"),
                          (BOB, 8, 1, "2026-11-22 08:15")]:
    db.add(CartItem(user_id=uid, product_id=pid, quantity=qty))
    sql.append(f"INSERT INTO cart_item (user_id, product_id, quantity, added_at) VALUES ({uid}, {pid}, {qty}, {lit(T(at))});")
db.commit()

n_orders = db.query(Order).count()
db.close()

header = f"""-- FUWA FUWA e-Shop：示範交易資料（由 backend/scripts/gen_demo_data.py 產生，請勿手動修改）
-- 共 {n_orders} 筆訂單，涵蓋 received、processing、shipping、closed、cancelled、returned 六種狀態，
-- 以及已核准（部分／全部）、已拒絕、待審核的退貨申請、商店評價與購物車。
-- 金額由後端金額計算服務產生（BR-09～BR-12），退款依 BR-26；依業務流程順序執行，所有 trigger 都會檢查。
-- 狀態歷程（order_status_history）由 trigger 自動寫入，這裡只把變更時間調整為情境中的時間。
"""
footer = f"""
-- 讓 SERIAL 從示範資料之後繼續編號
SELECT setval('orders_order_id_seq', (SELECT MAX(order_id) FROM orders));
SELECT setval('return_request_return_id_seq', (SELECT MAX(return_id) FROM return_request));
SELECT set_config('app.user_id', '', false);
"""
OUT.write_text(header + "\n".join(sql) + "\n" + footer)
with psycopg.connect("postgresql://fuwa:fuwa@localhost:5433/postgres", autocommit=True) as c:
    c.execute(f"DROP DATABASE IF EXISTS {SCRATCH} WITH (FORCE)")
print(f"wrote {OUT} ({n_orders} orders)")
