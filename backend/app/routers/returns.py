"""OMS 退貨：申請、查詢、核准、拒絕（OMS-F-011、OMS-F-012，BR-25、BR-26）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import check_order_store, get_current_user, require_customer, require_staff, staff_store_id, store_order_ids
from app.models import Order, ReturnRequest, User
from app.schemas_w2 import RejectIn, ReturnIn, return_json
from app.services import orders as svc

router = APIRouter()

STATUSES = ("pending", "approved", "rejected")


def fresh(db: Session, return_id: int) -> dict:
    db.expire_all()
    return return_json(db, db.get(ReturnRequest, return_id))


def load_return(db: Session, return_id: int) -> ReturnRequest:
    rr = db.get(ReturnRequest, return_id)
    if rr is None:
        raise HTTPException(404, "找不到退貨申請")
    return rr


@router.post("/", status_code=201)
def create(body: ReturnIn, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    order = db.get(Order, body.order_id)
    if order is None:
        raise HTTPException(404, "找不到訂單")
    if order.user_id != user.user_id:
        raise HTTPException(403, "BR-21：只能為自己的訂單申請退貨")
    reason = body.reason.strip()
    if not reason:
        raise HTTPException(422, "OMS-F-011：請填寫退貨原因")
    rr = svc.create_return(db, order, reason, [(i.item_no, i.return_qty) for i in body.items])
    db.commit()
    return fresh(db, rr.return_id)


@router.get("/mine")
def mine(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    rows = db.scalars(select(ReturnRequest).join(Order, Order.order_id == ReturnRequest.order_id)
                      .where(Order.user_id == user.user_id).order_by(ReturnRequest.requested_at.desc()))
    return [return_json(db, rr) for rr in rows.unique()]


@router.get("/")
def list_returns(status: str | None = None, _: User = Depends(require_staff), db: Session = Depends(get_db)):
    stmt = select(ReturnRequest)
    store_id = staff_store_id(db, _)
    if store_id is not None:
        stmt = stmt.where(ReturnRequest.order_id.in_(store_order_ids(store_id)))
    if status:
        if status not in STATUSES:
            raise HTTPException(422, "status 必須是 pending、approved 或 rejected")
        stmt = stmt.where(ReturnRequest.status == status)
    # 待審核的排前面，其餘依申請時間新到舊
    stmt = stmt.order_by((ReturnRequest.status != "pending"), ReturnRequest.requested_at.desc())
    return [return_json(db, rr) for rr in db.scalars(stmt).unique()]


@router.get("/{return_id}")
def get_return(return_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rr = load_return(db, return_id)
    check_order_store(db, user, rr.order_id)
    if rr.order.user_id != user.user_id and not user.has_role("staff"):
        raise HTTPException(403, "BR-21：只能查看自己的退貨申請")
    return return_json(db, rr)


@router.post("/{return_id}/approve")
def approve(return_id: int, user: User = Depends(require_staff), db: Session = Depends(get_db)):
    rr = load_return(db, return_id)
    check_order_store(db, user, rr.order_id)
    svc.approve_return(db, rr, user)
    db.commit()
    return fresh(db, return_id)


@router.post("/{return_id}/reject")
def reject(return_id: int, body: RejectIn, user: User = Depends(require_staff), db: Session = Depends(get_db)):
    rr = load_return(db, return_id)
    check_order_store(db, user, rr.order_id)
    svc.reject_return(db, rr, user, body.reject_reason)
    db.commit()
    return fresh(db, return_id)
