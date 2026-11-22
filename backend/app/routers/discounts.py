"""DMS 折扣管理子系統（BR-13～BR-18、BR-20、DMS-F-001～009）。"""
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import deps
from app.db import get_db
from app.models import Discount, OrderDiscount, Product, ProductDiscount, User

router = APIRouter()


class DiscountCreate(BaseModel):
    discount_type: str
    description: str
    start_date: date
    end_date: date
    rate: float | None = None
    min_amount: int | None = None
    buy_qty: int | None = None
    free_qty: int | None = None
    is_active: bool = True
    product_ids: list[int] | None = None


class DiscountUpdate(BaseModel):
    discount_code: str | None = None
    discount_type: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    rate: float | None = None
    min_amount: int | None = None
    buy_qty: int | None = None
    free_qty: int | None = None
    is_active: bool | None = None
    product_ids: list[int] | None = None


def format_discounts(db: Session, discounts: list[Discount]) -> list[dict[str, Any]]:
    if not discounts:
        return []
    codes = [d.discount_code for d in discounts]
    used_rows = db.execute(
        select(OrderDiscount.discount_code, func.count(OrderDiscount.order_id))
        .where(OrderDiscount.discount_code.in_(codes))
        .group_by(OrderDiscount.discount_code)
    ).all()
    used_map = {code: count for code, count in used_rows}

    today = date.today()
    results = []
    for d in discounts:
        prods = [
            {"product_id": pd.product_id, "name": pd.product.name}
            for pd in sorted(d.products, key=lambda x: x.product_id)
        ]
        is_current = bool(d.is_active and d.start_date <= today <= d.end_date)
        results.append({
            "discount_code": d.discount_code,
            "discount_type": d.discount_type,
            "description": d.description,
            "start_date": d.start_date.isoformat(),
            "end_date": d.end_date.isoformat(),
            "rate": float(d.rate) if d.rate is not None else None,
            "min_amount": int(d.min_amount) if d.min_amount is not None else None,
            "buy_qty": int(d.buy_qty) if d.buy_qty is not None else None,
            "free_qty": int(d.free_qty) if d.free_qty is not None else None,
            "is_active": d.is_active,
            "products": prods,
            "used_count": used_map.get(d.discount_code, 0),
            "is_current": is_current,
        })
    return results


def validate_discount_rules(
    db: Session,
    discount_type: str,
    start_date: date,
    end_date: date,
    rate: float | None,
    min_amount: int | None,
    buy_qty: int | None,
    free_qty: int | None,
    product_ids: list[int] | None,
    exclude_code: str | None = None,
) -> list[Product]:
    if discount_type not in ("shipping", "seasonal", "special_event"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "折扣類型無效")

    if start_date > end_date:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-14：開始日期須小於或等於結束日期")

    if rate is not None and not (0 < rate < 1):
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-15：折扣率須介於 0 與 1 之間")

    matched_products: list[Product] = []

    if discount_type == "shipping":
        if min_amount is None or min_amount <= 0:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-17：運費折扣的門檻金額須大於 0")
        if rate is not None or buy_qty is not None or free_qty is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-17：運費折扣不可設定折扣率或買送數量")
        if product_ids:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：只有特殊活動折扣可以指定商品")

    elif discount_type == "seasonal":
        if rate is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-15：季節性折扣須設定折扣率")
        if min_amount is not None or buy_qty is not None or free_qty is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-15：季節性折扣不可設定門檻金額或買送數量")
        if product_ids:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：只有特殊活動折扣可以指定商品")

    elif discount_type == "special_event":
        if min_amount is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：特殊活動折扣不可設定門檻金額")

        has_rate = rate is not None
        has_bogo = buy_qty is not None or free_qty is not None

        if has_rate and has_bogo:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：特殊活動折扣須設定折扣率或買送數量（二擇一）")
        if not has_rate and not has_bogo:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：特殊活動折扣須設定折扣率或買送數量（二擇一）")

        if has_bogo:
            if buy_qty is None or free_qty is None or buy_qty <= 0 or free_qty <= 0:
                raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：買送數量須為大於 0 的整數")

        if not product_ids:
            raise HTTPException(status.HTTP_409_CONFLICT, "BR-16：特殊活動折扣至少須指定一項商品")

        # Verify products exist
        existing = {
            p.product_id: p
            for p in db.scalars(select(Product).where(Product.product_id.in_(product_ids))).all()
        }
        for pid in product_ids:
            if pid not in existing:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"PMS：找不到商品 ID {pid}")
            matched_products.append(existing[pid])

        # Overlap check for special_event (BR-13, DMS-F-008)
        for prod in matched_products:
            conflict_stmt = (
                select(ProductDiscount)
                .join(Discount, Discount.discount_code == ProductDiscount.discount_code)
                .where(
                    ProductDiscount.product_id == prod.product_id,
                    Discount.start_date <= end_date,
                    Discount.end_date >= start_date,
                )
            )
            if exclude_code is not None:
                conflict_stmt = conflict_stmt.where(ProductDiscount.discount_code != exclude_code)
            conflict = db.scalars(conflict_stmt).first()
            if conflict is not None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"BR-13：商品「{prod.name}」在該期間已有特殊活動折扣 {conflict.discount_code}，期間不得重疊",
                )

    return matched_products


@router.get("/active")
def get_active_discounts(db: Session = Depends(get_db)):
    """首頁展示今天有效的折扣（公開無須登入）。"""
    today = date.today()
    discounts = list(
        db.scalars(
            select(Discount)
            .where(
                Discount.is_active.is_(True),
                Discount.start_date <= today,
                Discount.end_date >= today,
            )
            .order_by(Discount.discount_code)
        )
    )
    return format_discounts(db, discounts)


@router.get("/")
def list_discounts(
    type: str | None = Query(None),
    active_on: date | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """查詢折扣清單（staff）。"""
    stmt = select(Discount)
    if type:
        stmt = stmt.where(Discount.discount_type == type)
    if active_on:
        stmt = stmt.where(
            Discount.is_active.is_(True),
            Discount.start_date <= active_on,
            Discount.end_date >= active_on,
        )
    if q:
        term = f"%{q}%"
        stmt = stmt.where(Discount.discount_code.ilike(term) | Discount.description.ilike(term))
    stmt = stmt.order_by(Discount.discount_code)
    discounts = list(db.scalars(stmt))
    return format_discounts(db, discounts)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_discount(
    body: DiscountCreate,
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """建立折扣（staff）。"""
    pids = list(dict.fromkeys(body.product_ids)) if body.product_ids is not None else None

    validate_discount_rules(
        db=db,
        discount_type=body.discount_type,
        start_date=body.start_date,
        end_date=body.end_date,
        rate=body.rate,
        min_amount=body.min_amount,
        buy_qty=body.buy_qty,
        free_qty=body.free_qty,
        product_ids=pids,
    )

    prefix_map = {
        "shipping": "SHP",
        "seasonal": "SEA",
        "special_event": "EVT",
    }
    prefix = prefix_map[body.discount_type]
    seq = db.scalar(text("SELECT nextval('discount_code_seq')"))
    discount_code = f"{prefix}-{seq:04d}"

    discount = Discount(
        discount_code=discount_code,
        discount_type=body.discount_type,
        description=body.description,
        start_date=body.start_date,
        end_date=body.end_date,
        rate=Decimal(str(body.rate)) if body.rate is not None else None,
        min_amount=Decimal(body.min_amount) if body.min_amount is not None else None,
        buy_qty=body.buy_qty,
        free_qty=body.free_qty,
        is_active=body.is_active,
    )
    db.add(discount)
    db.flush()

    if body.discount_type == "special_event" and pids:
        for pid in pids:
            pd = ProductDiscount(product_id=pid, discount_code=discount_code)
            db.add(pd)
        db.flush()

    db.commit()
    db.refresh(discount)
    return format_discounts(db, [discount])[0]


@router.get("/{code}")
def get_discount(
    code: str,
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """取得單一折扣詳情（staff）。"""
    discount = db.get(Discount, code)
    if discount is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到折扣代碼 {code}")
    return format_discounts(db, [discount])[0]


@router.put("/{code}")
def update_discount(
    code: str,
    body: DiscountUpdate,
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """修改折扣（staff，代碼與類型不可變更）。"""
    discount = db.get(Discount, code)
    if discount is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到折扣代碼 {code}")

    if body.discount_code is not None and body.discount_code != code:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-18：折扣代碼與類型建立後不可修改")
    if body.discount_type is not None and body.discount_type != discount.discount_type:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-18：折扣代碼與類型建立後不可修改")

    fields = body.model_fields_set

    merged_start = body.start_date if "start_date" in fields and body.start_date is not None else discount.start_date
    merged_end = body.end_date if "end_date" in fields and body.end_date is not None else discount.end_date
    merged_desc = body.description if "description" in fields and body.description is not None else discount.description
    merged_active = body.is_active if "is_active" in fields and body.is_active is not None else discount.is_active

    merged_rate = body.rate if "rate" in fields else (float(discount.rate) if discount.rate is not None else None)
    merged_min = body.min_amount if "min_amount" in fields else (int(discount.min_amount) if discount.min_amount is not None else None)
    merged_buy = body.buy_qty if "buy_qty" in fields else discount.buy_qty
    merged_free = body.free_qty if "free_qty" in fields else discount.free_qty

    if "product_ids" in fields:
        merged_pids = list(dict.fromkeys(body.product_ids)) if body.product_ids is not None else []
    else:
        merged_pids = [pd.product_id for pd in discount.products]

    validate_discount_rules(
        db=db,
        discount_type=discount.discount_type,
        start_date=merged_start,
        end_date=merged_end,
        rate=merged_rate,
        min_amount=merged_min,
        buy_qty=merged_buy,
        free_qty=merged_free,
        product_ids=merged_pids if discount.discount_type == "special_event" else None,
        exclude_code=code,
    )

    discount.description = merged_desc
    discount.start_date = merged_start
    discount.end_date = merged_end
    discount.rate = Decimal(str(merged_rate)) if merged_rate is not None else None
    discount.min_amount = Decimal(merged_min) if merged_min is not None else None
    discount.buy_qty = merged_buy
    discount.free_qty = merged_free
    discount.is_active = merged_active

    if discount.discount_type == "special_event":
        target_pids = set(merged_pids)
        for pd in list(discount.products):
            if pd.product_id not in target_pids:
                db.delete(pd)
                discount.products.remove(pd)

        existing_pids = {pd.product_id for pd in discount.products}
        for pid in target_pids - existing_pids:
            pd = ProductDiscount(product_id=pid, discount_code=code)
            discount.products.append(pd)

    db.commit()
    db.refresh(discount)
    return format_discounts(db, [discount])[0]


@router.delete("/{code}")
def delete_discount(
    code: str,
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """刪除折扣（staff，已使用的不可刪除，BR-20）。"""
    discount = db.get(Discount, code)
    if discount is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"找不到折扣代碼 {code}")

    used = db.scalar(
        select(func.count(OrderDiscount.order_id)).where(OrderDiscount.discount_code == code)
    )
    if used and used > 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-20：此折扣已被訂單使用，只能停用或提前結束")

    db.delete(discount)
    db.commit()
    return {"ok": True, "discount_code": code}
