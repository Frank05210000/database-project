"""OMS 訂單：結帳預覽、結帳、查詢、取消、狀態流轉（OMS-F-001～OMS-F-010，BR-07、BR-19、BR-21、BR-25）。

業務邏輯都在 services/orders.py，這裡只做授權、交易提交與輸出格式。
"""
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import check_order_store, get_current_user, require_customer, require_staff, staff_store_id, store_order_ids
from app.models import Order, User
from app.schemas_w2 import CheckoutIn, StatusIn, order_json, order_summary_json
from app.services import orders as svc

router = APIRouter()


def load_order(db: Session, order_id: int, user: User) -> Order:
    """本人或工作人員可看；其他人 403（BR-21）。"""
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "找不到訂單")
    if order.user_id != user.user_id and not user.has_role("staff"):
        raise HTTPException(403, "BR-21：只能查看自己的訂單")
    if order.user_id != user.user_id:   # 店員看別人的訂單時，限含本店商品的訂單
        check_order_store(db, user, order_id)
    return order


def fresh(db: Session, order_id: int) -> dict:
    """commit 後重新讀取，讓 viewonly 的 history / return_request 反映最新狀態。"""
    db.expire_all()
    return order_json(db, db.get(Order, order_id))


@router.get("/checkout-preview")
def checkout_preview(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    _, q = svc.cart_quote(db, user)
    return {"quote": q.as_dict(),
            "recipient": {"name": user.name, "phone": user.phone or "", "address": user.address or ""}}


@router.post("/", status_code=201)
def create_order(body: CheckoutIn, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    if not (body.recipient_name.strip() and body.recipient_phone.strip() and body.recipient_address.strip()):
        raise HTTPException(422, "OMS-F-003：請填寫收件人姓名、電話與地址")
    order = svc.checkout(db, user, body.recipient_name.strip(), body.recipient_phone.strip(),
                         body.recipient_address.strip())
    db.commit()
    return fresh(db, order.order_id)


@router.get("/mine")
def my_orders(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    rows = db.scalars(select(Order).where(Order.user_id == user.user_id)
                      .order_by(Order.order_time.desc(), Order.order_id.desc()))
    return [order_summary_json(o) for o in rows]


@router.get("/")
def list_orders(status: str | None = None, date_from: date | None = None, date_to: date | None = None,
                q: str | None = None, _: User = Depends(require_staff), db: Session = Depends(get_db)):
    stmt = select(Order).join(User, User.user_id == Order.user_id)
    store_id = staff_store_id(db, _)
    if store_id is not None:
        stmt = stmt.where(Order.order_id.in_(store_order_ids(store_id)))
    if status:
        stmt = stmt.where(Order.status == status)
    if date_from:
        stmt = stmt.where(Order.order_time >= datetime.combine(date_from, time.min))
    if date_to:
        stmt = stmt.where(Order.order_time < datetime.combine(date_to + timedelta(days=1), time.min))
    if q and q.strip():
        kw = q.strip()
        like = f"%{kw}%"
        conds = [User.loginid.ilike(like), User.name.ilike(like), cast(Order.order_id, String) == kw]
        stmt = stmt.where(or_(*conds))
    stmt = stmt.order_by(Order.order_time.desc(), Order.order_id.desc())
    return [order_summary_json(o) for o in db.scalars(stmt).unique()]


@router.get("/{order_id}")
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return order_json(db, load_order(db, order_id, user))


@router.post("/{order_id}/cancel")
def cancel(order_id: int, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "找不到訂單")
    if order.user_id != user.user_id:
        raise HTTPException(403, "BR-21：只能取消自己的訂單")
    svc.cancel_order(db, order, user)
    db.commit()
    return fresh(db, order_id)


@router.post("/{order_id}/status")
def change_status(order_id: int, body: StatusIn, user: User = Depends(require_staff),
                  db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(404, "找不到訂單")
    check_order_store(db, user, order_id)
    svc.advance_status(db, order, user, body.status)
    db.commit()
    return fresh(db, order_id)
