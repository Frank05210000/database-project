"""訂單交易：結帳（OMS-F-003）、取消（OMS-F-010）、狀態流轉（BR-19）、退貨與退款（BR-25、BR-26）。

每個函式都在呼叫端的交易中執行，最後由呼叫端 commit；任何一步失敗就整筆回復。
資料庫 trigger 會再檢查一次相同規則（02_triggers.sql）。
"""
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import set_actor
from app.models import (CartItem, Order, OrderDiscount, OrderItem, Product, ReturnItem, ReturnRequest, User)
from app.services.pricing import PriceQuote, quote, round_half_up

NEXT_STATUS = {"received": "processing", "processing": "shipping", "shipping": "closed"}


def conflict(msg: str) -> HTTPException:
    return HTTPException(status_code=409, detail=msg)


def cart_quote(db: Session, user: User, on: date | None = None) -> tuple[list[CartItem], PriceQuote]:
    items = list(db.scalars(select(CartItem).where(CartItem.user_id == user.user_id)
                            .order_by(CartItem.added_at, CartItem.product_id)))
    return items, quote(db, [(ci.product, ci.quantity) for ci in items], on or date.today())


def checkout(db: Session, user: User, recipient_name: str, recipient_phone: str, recipient_address: str,
             order_time: datetime | None = None) -> Order:
    """把購物車變成訂單。order_time 只給種子資料用，正常結帳為現在。"""
    set_actor(db, user.user_id)
    now = order_time or datetime.now()
    cart = list(db.scalars(select(CartItem).where(CartItem.user_id == user.user_id)
                           .order_by(CartItem.added_at, CartItem.product_id)))
    if not cart:
        raise conflict("BR-07：購物車是空的，訂單至少要有一項商品")

    # BR-06：鎖定商品列，避免兩人同時買最後一件
    ids = [ci.product_id for ci in cart]
    products = {p.product_id: p for p in db.scalars(
        select(Product).where(Product.product_id.in_(ids)).order_by(Product.product_id)
        .with_for_update(of=Product).execution_options(populate_existing=True))}
    pairs = []
    for ci in cart:
        p = products[ci.product_id]
        if not p.is_listed:
            raise conflict(f"PMS：商品「{p.name}」已下架，請從購物車移除")
        if ci.quantity > p.stock:
            raise conflict(f"BR-06：商品「{p.name}」庫存只剩 {p.stock}，少於購買數量 {ci.quantity}")
        pairs.append((p, ci.quantity))

    q = quote(db, pairs, now.date())  # BR-14：以付款日期判斷折扣是否有效
    order = Order(user_id=user.user_id, order_time=now, paid_at=now,
                  recipient_name=recipient_name, recipient_phone=recipient_phone,
                  recipient_address=recipient_address, subtotal=q.subtotal, discount_total=q.discount_total,
                  tax=q.tax, shipping_fee=q.shipping_fee, status="received")
    for no, line in enumerate(q.lines, start=1):
        order.items.append(OrderItem(item_no=no, product_id=line.product_id, product_name=line.product_name,
                                     unit_price=line.unit_price, quantity=line.quantity,
                                     event_discount=line.event_discount))
    for ad in q.applied:
        order.discounts.append(OrderDiscount(discount_code=ad.discount_code, amount=ad.amount))
    db.add(order)
    for p, qty in pairs:
        p.stock -= qty
    for ci in cart:
        db.delete(ci)
    db.flush()
    db.refresh(order, ["total"])
    return order


def cancel_order(db: Session, order: Order, actor: User) -> Order:
    """顧客取消 received 的訂單並回補庫存（BR-19、OMS-F-010）。"""
    if order.status != "received":
        raise conflict(f"BR-19：只有 received 的訂單可以取消（目前為 {order.status}）")
    set_actor(db, actor.user_id)
    order.status = "cancelled"
    for it in order.items:
        it.product.stock += it.quantity
    db.flush()
    db.expire(order, ["history"])
    return order


def advance_status(db: Session, order: Order, actor: User, new_status: str) -> Order:
    """工作人員依序推進訂單狀態（BR-19、OMS-F-007）。"""
    expected = NEXT_STATUS.get(order.status)
    if expected is None or new_status != expected:
        raise conflict(f"BR-19：訂單狀態不可由 {order.status} 變更為 {new_status}"
                       + (f"，下一步只能是 {expected}" if expected else ""))
    if order.return_request is not None and order.return_request.status == "pending":
        raise conflict("BR-25：訂單有待審核的退貨申請，不可更新狀態")
    set_actor(db, actor.user_id)
    order.status = new_status
    db.flush()
    db.expire(order, ["history"])
    return order


def create_return(db: Session, order: Order, reason: str, items: list[tuple[int, int]]) -> ReturnRequest:
    """顧客申請退貨；items 為 (item_no, return_qty)（BR-25、OMS-F-011）。"""
    if order.status not in ("processing", "shipping", "closed"):
        raise conflict(f"BR-25：只有 processing、shipping、closed 的訂單可以申請退貨（目前為 {order.status}）")
    if order.return_request is not None:
        raise conflict("BR-25：每筆訂單只能提出一次退貨申請")
    if not items:
        raise conflict("BR-25：請至少選擇一項要退的商品")
    by_no = {it.item_no: it for it in order.items}
    seen = set()
    for item_no, qty in items:
        if item_no not in by_no:
            raise conflict(f"BR-25：訂單沒有第 {item_no} 項商品")
        if item_no in seen:
            raise conflict("BR-25：同一項商品只能出現一次")
        seen.add(item_no)
        if qty <= 0:
            raise conflict("BR-25：退貨數量須為大於 0 的整數")
        if qty > by_no[item_no].quantity:
            raise conflict(f"BR-25：「{by_no[item_no].product_name}」退貨數量 {qty} 超過購買數量 {by_no[item_no].quantity}")
    rr = ReturnRequest(order_id=order.order_id, reason=reason, status="pending")
    db.add(rr)
    db.flush()
    for item_no, qty in items:
        rr.items.append(ReturnItem(order_id=order.order_id, item_no=item_no, return_qty=qty))
    db.flush()
    db.expire(order, ["return_request"])
    return rr


def net_shipping(order: Order) -> Decimal:
    """顧客實際付的運費 = 基本運費 − 運費折扣。"""
    ship_disc = sum((od.amount for od in order.discounts if od.discount.discount_type == "shipping"), Decimal(0))
    return Decimal(order.shipping_fee) - ship_disc


def compute_refund(order: Order, rr: ReturnRequest) -> tuple[dict[int, Decimal], Decimal, bool]:
    """BR-26 比例分攤退款。回傳 (各明細退款, 退款總額, 是否全部退貨)。

    每項退款 = (訂單總額 − 實付運費) × 該項退貨商品扣除特殊活動折扣後的金額 ÷ 全部商品扣除特殊活動折扣後的金額
    部分數量退貨時，「該項退貨商品扣除特殊活動折扣後的金額」依退貨數量比例計算。
    運費不退；唯一例外是 processing 時全部退貨，運費一併退還（加在退款總額）。
    """
    ship = net_shipping(order)
    base = Decimal(order.total) - ship
    by_no = {it.item_no: it for it in order.items}
    all_net = sum((it.unit_price * it.quantity - it.event_discount for it in order.items), Decimal(0))
    refunds: dict[int, Decimal] = {}
    for ri in rr.items:
        it = by_no[ri.item_no]
        item_net = (it.unit_price * it.quantity - it.event_discount) * Decimal(ri.return_qty) / Decimal(it.quantity)
        refunds[ri.item_no] = round_half_up(base * item_net / all_net) if all_net > 0 else Decimal(0)
    returned = {ri.item_no: ri.return_qty for ri in rr.items}
    full = all(returned.get(it.item_no, 0) >= it.quantity for it in order.items)
    total = sum(refunds.values(), Decimal(0))
    if full and order.status == "processing":
        total += ship
    return refunds, total, full


def approve_return(db: Session, rr: ReturnRequest, actor: User) -> ReturnRequest:
    """核准退貨：回補庫存、計算退款，全部退貨時訂單改為 returned（OMS-F-012）。"""
    if rr.status != "pending":
        raise conflict(f"BR-25：退貨申請已處理（{rr.status}）")
    set_actor(db, actor.user_id)
    order = rr.order
    refunds, total, full = compute_refund(order, rr)
    by_no = {it.item_no: it for it in order.items}
    for ri in rr.items:
        ri.refund_amount = refunds[ri.item_no]
        by_no[ri.item_no].product.stock += ri.return_qty
    rr.status, rr.processed_by, rr.processed_at, rr.refund_total = "approved", actor.user_id, datetime.now(), total
    db.flush()
    if full:
        order.status = "returned"
        db.flush()
        db.expire(order, ["history"])
    return rr


def reject_return(db: Session, rr: ReturnRequest, actor: User, reject_reason: str) -> ReturnRequest:
    if rr.status != "pending":
        raise conflict(f"BR-25：退貨申請已處理（{rr.status}）")
    if not reject_reason or not reject_reason.strip():
        raise conflict("OMS-F-012：拒絕退貨須填寫拒絕原因")
    set_actor(db, actor.user_id)
    rr.status, rr.processed_by, rr.processed_at, rr.reject_reason = "rejected", actor.user_id, datetime.now(), reject_reason.strip()
    db.flush()
    return rr
