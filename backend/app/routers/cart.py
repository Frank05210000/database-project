"""SCS 購物車（SCS-F-001～SCS-F-006，BR-05、BR-06、BR-21）。每個寫入操作都回傳完整購物車。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_customer
from app.models import CartItem, Product, User
from app.schemas_w2 import CartAddIn, CartQtyIn, cart_json

router = APIRouter()


def _check_qty(db: Session, product_id: int, quantity: int) -> Product:
    """BR-05 數量為正整數、BR-06 不超過庫存、下架商品不可購買。"""
    if quantity <= 0:
        raise HTTPException(409, "BR-05：數量必須是大於 0 的整數")
    p = db.get(Product, product_id)
    if p is None:
        raise HTTPException(404, "找不到商品")
    if not p.is_listed:
        raise HTTPException(409, f"PMS：商品「{p.name}」已下架，不能加入購物車")
    if quantity > p.stock:
        raise HTTPException(409, f"BR-06：商品「{p.name}」庫存只剩 {p.stock}，購物車數量 {quantity} 超過庫存")
    return p


def _result(db: Session, user: User) -> dict:
    db.expire_all()
    return cart_json(db, user)


@router.get("/")
def get_cart(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    return cart_json(db, user)


@router.post("/items")
def add_item(body: CartAddIn, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    if body.quantity <= 0:
        raise HTTPException(409, "BR-05：數量必須是大於 0 的整數")
    ci = db.get(CartItem, (user.user_id, body.product_id))
    total = body.quantity + (ci.quantity if ci else 0)
    _check_qty(db, body.product_id, total)
    if ci:
        ci.quantity = total
    else:
        db.add(CartItem(user_id=user.user_id, product_id=body.product_id, quantity=total))
    db.commit()
    return _result(db, user)


@router.put("/items/{product_id}")
def set_item(product_id: int, body: CartQtyIn, user: User = Depends(require_customer),
             db: Session = Depends(get_db)):
    ci = db.get(CartItem, (user.user_id, product_id))
    if ci is None:
        raise HTTPException(404, "購物車中沒有這項商品")
    _check_qty(db, product_id, body.quantity)
    ci.quantity = body.quantity
    db.commit()
    return _result(db, user)


@router.delete("/items/{product_id}")
def remove_item(product_id: int, user: User = Depends(require_customer), db: Session = Depends(get_db)):
    ci = db.get(CartItem, (user.user_id, product_id))
    if ci is None:
        raise HTTPException(404, "購物車中沒有這項商品")
    db.delete(ci)
    db.commit()
    return _result(db, user)


@router.delete("/")
def clear_cart(user: User = Depends(require_customer), db: Session = Depends(get_db)):
    db.execute(delete(CartItem).where(CartItem.user_id == user.user_id))
    db.commit()
    return _result(db, user)
