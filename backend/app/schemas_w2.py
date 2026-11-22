"""SCS / OMS 用的請求模型與 JSON 序列化（API 契約 §5，金額一律轉成 int）。"""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import Discount, Order, Product, ReturnRequest, User
from app.services import orders as svc
from app.services.pricing import event_discount_for
from app.clock import tw_now, tw_today  # noqa: F401


# ---------- 請求 ----------
class CartAddIn(BaseModel):
    product_id: int
    quantity: int


class CartQtyIn(BaseModel):
    quantity: int


class CheckoutIn(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=50)
    recipient_phone: str = Field(min_length=1, max_length=20)
    recipient_address: str = Field(min_length=1, max_length=200)


class StatusIn(BaseModel):
    status: str


class ReturnItemIn(BaseModel):
    item_no: int
    return_qty: int


class ReturnIn(BaseModel):
    order_id: int
    reason: str = Field(min_length=1, max_length=300)
    items: list[ReturnItemIn]


class RejectIn(BaseModel):
    reject_reason: str = ""


# ---------- 輸出 ----------
def money(x: Decimal | int | None) -> int | None:
    return None if x is None else int(x)


def event_discount_json(d: Discount | None) -> dict | None:
    if d is None:
        return None
    return {"discount_code": d.discount_code, "description": d.description,
            "rate": float(d.rate) if d.rate is not None else None,
            "buy_qty": d.buy_qty, "free_qty": d.free_qty,
            "start_date": d.start_date, "end_date": d.end_date}


def product_json(db: Session, p: Product, on: date | None = None) -> dict:
    return {
        "product_id": p.product_id, "store_id": p.store_id, "store_name": p.store.name,
        "name": p.name, "description": p.description, "category": p.category, "image_url": p.image_url,
        "price": int(p.price), "stock": p.stock, "is_listed": p.is_listed,
        "created_at": p.created_at, "updated_at": p.updated_at,
        "event_discount": event_discount_json(event_discount_for(db, p.product_id, on or tw_today())),
    }


def cart_json(db: Session, user: User) -> dict:
    today = tw_today()
    items, q = svc.cart_quote(db, user, today)
    return {
        "items": [{"product": product_json(db, ci.product, today), "quantity": ci.quantity,
                   "added_at": ci.added_at, "line_subtotal": int(ci.product.price) * ci.quantity}
                  for ci in items],
        "quote": q.as_dict(),
    }


def customer_json(u: User) -> dict:
    return {"user_id": u.user_id, "loginid": u.loginid, "name": u.name}


def order_summary_json(o: Order) -> dict:
    rr = o.return_request
    return {
        "order_id": o.order_id, "order_time": o.order_time, "status": o.status, "total": money(o.total),
        "item_count": sum(it.quantity for it in o.items),
        "customer": customer_json(o.user),
        "has_return": rr is not None, "return_status": rr.status if rr else None,
    }


def return_json(db: Session, rr: ReturnRequest) -> dict:
    order = rr.order
    by_no = {it.item_no: it for it in order.items}
    processor = db.get(User, rr.processed_by) if rr.processed_by else None
    return {
        "return_id": rr.return_id, "order_id": rr.order_id, "requested_at": rr.requested_at,
        "reason": rr.reason, "status": rr.status,
        "processed_by_name": processor.name if processor else None,
        "processed_at": rr.processed_at, "reject_reason": rr.reject_reason,
        "refund_total": money(rr.refund_total),
        "customer": customer_json(order.user), "order_status": order.status, "order_total": money(order.total),
        "items": [{"item_no": ri.item_no, "product_name": by_no[ri.item_no].product_name,
                   "unit_price": money(by_no[ri.item_no].unit_price), "quantity": by_no[ri.item_no].quantity,
                   "return_qty": ri.return_qty, "refund_amount": money(ri.refund_amount)} for ri in rr.items],
    }


TYPE_ORDER = {"special_event": 0, "seasonal": 1, "shipping": 2}  # 與 BR-10 計算順序一致


def order_json(db: Session, o: Order) -> dict:
    rr = o.return_request
    pending = rr is not None and rr.status == "pending"
    ship_disc = sum((od.amount for od in o.discounts if od.discount.discount_type == "shipping"), Decimal(0))
    data = order_summary_json(o)
    data.update({
        "recipient_name": o.recipient_name, "recipient_phone": o.recipient_phone,
        "recipient_address": o.recipient_address,
        "subtotal": money(o.subtotal), "discount_total": money(o.discount_total), "tax": money(o.tax),
        "shipping_fee": money(o.shipping_fee), "shipping_discount": money(ship_disc), "paid_at": o.paid_at,
        "items": [{"item_no": it.item_no, "product_id": it.product_id, "product_name": it.product_name,
                   "image_url": it.product.image_url, "store_name": it.product.store.name,
                   "unit_price": money(it.unit_price), "quantity": it.quantity,
                   "line_subtotal": money(it.line_subtotal), "event_discount": money(it.event_discount)}
                  for it in o.items],
        "discounts": [{"discount_code": od.discount_code, "discount_type": od.discount.discount_type,
                       "description": od.discount.description, "amount": money(od.amount)}
                      for od in sorted(o.discounts, key=lambda d: (TYPE_ORDER.get(d.discount.discount_type, 9),
                                                                   d.discount_code))],
        "history": [{"seq_no": h.seq_no, "status": h.status, "changed_at": h.changed_at,
                     "changed_by_name": h.changer.name} for h in o.history],
        "return_request": return_json(db, rr) if rr else None,
        "next_status": None if pending else svc.NEXT_STATUS.get(o.status),
        "can_cancel": o.status == "received",
        "can_return": o.status in ("processing", "shipping", "closed") and rr is None,
    })
    return data
