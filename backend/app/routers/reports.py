"""RSS 報表統計子系統（BR-23、RSS-F-001～005）。"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import deps
from app.db import get_db
from app.models import Order, ReturnRequest, Store, User
from app.services.pricing import round_half_up
from app.clock import tw_now, tw_today  # noqa: F401

router = APIRouter()


@router.get("/sales")
def get_sales_report(
    period: str = Query("day"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    store_id: int | None = Query(None),
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """銷售報表（staff，依 BR-23 比例分攤，排除 cancelled 與 returned 訂單）。"""
    if period not in ("day", "week", "month"):
        raise HTTPException(422, "period 必須是 day、week 或 month")

    own_store = deps.staff_store_id(db, staff)
    if own_store is not None:
        store_id = own_store
    today = tw_today()
    if date_to is None:
        date_to = today
    if date_from is None:
        date_from = date_to - timedelta(days=30)

    # Filter by orders.order_time date
    stmt = (
        select(Order)
        .where(
            Order.status.not_in(["cancelled", "returned"]),
            Order.order_time >= datetime.combine(date_from, time.min),
            Order.order_time <= datetime.combine(date_to, time.max),
        )
        .order_by(Order.order_time)
    )
    orders = list(db.scalars(stmt))

    stores = {s.store_id: s.name for s in db.scalars(select(Store)).all()}

    # agg: (p_start, p_label, store_id) -> {"order_ids": set(), "sales_total": Decimal(0)}
    agg: dict[tuple[str, str, int], dict[str, Any]] = {}

    for order in orders:
        order_date = order.order_time.date()
        if period == "day":
            p_start = order_date.isoformat()
            p_label = order_date.isoformat()
        elif period == "week":
            monday = order_date - timedelta(days=order_date.weekday())
            sunday = monday + timedelta(days=6)
            iso_year, iso_week, _ = monday.isocalendar()
            p_start = monday.isoformat()
            p_label = f"{iso_year}-W{iso_week:02d} ({monday.strftime('%m/%d')}–{sunday.strftime('%m/%d')})"
        else:  # month
            first_day = date(order_date.year, order_date.month, 1)
            p_start = first_day.isoformat()
            p_label = f"{order_date.year:04d}-{order_date.month:02d}"

        order_net = sum(
            (it.unit_price * it.quantity - it.event_discount for it in order.items),
            Decimal(0),
        )
        store_items: dict[int, Decimal] = {}
        for it in order.items:
            sid = it.product.store_id
            net = it.unit_price * it.quantity - it.event_discount
            store_items[sid] = store_items.get(sid, Decimal(0)) + net

        for sid, s_net in store_items.items():
            if order_net > 0:
                share = round_half_up(Decimal(order.total) * s_net / order_net)
            else:
                share = Decimal(0)
            key = (p_start, p_label, sid)
            entry = agg.setdefault(key, {"order_ids": set(), "sales_total": Decimal(0)})
            entry["order_ids"].add(order.order_id)
            entry["sales_total"] += share

        # Partially returned orders (return_request.status='approved' while order not 'returned')
        if (
            order.return_request is not None
            and order.return_request.status == "approved"
            and order.status != "returned"
        ):
            item_store_map = {it.item_no: it.product.store_id for it in order.items}
            for ri in order.return_request.items:
                sid = item_store_map.get(ri.item_no)
                if sid is not None and ri.refund_amount is not None:
                    key = (p_start, p_label, sid)
                    entry = agg.setdefault(key, {"order_ids": set(), "sales_total": Decimal(0)})
                    entry["sales_total"] -= Decimal(ri.refund_amount)

    rows = []
    for (p_start, p_label, sid), data in agg.items():
        if store_id is not None and sid != store_id:
            continue
        rows.append({
            "period_start": p_start,
            "period_label": p_label,
            "store_id": sid,
            "store_name": stores.get(sid, f"Store {sid}"),
            "order_count": len(data["order_ids"]),
            "sales_total": int(data["sales_total"]),
        })

    rows.sort(key=lambda r: (r["period_start"], r["store_id"]))
    return rows


@router.get("/top-products")
def get_top_products(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    store_id: int | None = Query(None),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """暢銷商品報表（staff，排除 cancelled 與 returned 訂單）。"""
    own_store = deps.staff_store_id(db, staff)
    if own_store is not None:
        store_id = own_store
    stmt = select(Order).where(Order.status.not_in(["cancelled", "returned"]))
    if date_from:
        stmt = stmt.where(Order.order_time >= datetime.combine(date_from, time.min))
    if date_to:
        stmt = stmt.where(Order.order_time <= datetime.combine(date_to, time.max))

    orders = list(db.scalars(stmt))

    prod_agg: dict[int, dict[str, Any]] = {}
    for order in orders:
        for it in order.items:
            sid = it.product.store_id
            if store_id is not None and sid != store_id:
                continue
            pid = it.product_id
            if pid not in prod_agg:
                prod_agg[pid] = {
                    "store_id": sid,
                    "store_name": it.product.store.name,
                    "product_id": pid,
                    "product_name": it.product_name,
                    "quantity": 0,
                    "revenue": Decimal(0),
                }
            prod_agg[pid]["quantity"] += it.quantity
            prod_agg[pid]["revenue"] += it.unit_price * it.quantity - it.event_discount

    rows = [
        {
            "store_id": v["store_id"],
            "store_name": v["store_name"],
            "product_id": v["product_id"],
            "product_name": v["product_name"],
            "quantity": v["quantity"],
            "revenue": int(v["revenue"]),
        }
        for v in prod_agg.values()
    ]
    rows.sort(key=lambda r: (-r["quantity"], -r["revenue"], r["product_id"]))
    return rows[:limit]


@router.get("/summary")
def get_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
    staff: User = Depends(deps.require_staff),
):
    """營運摘要（staff，銷售總額依 BR-23 各商店分攤加總）。"""
    store_id = deps.staff_store_id(db, staff)
    stmt = select(Order)
    if store_id is not None:
        stmt = stmt.where(Order.order_id.in_(deps.store_order_ids(store_id)))
    if date_from:
        stmt = stmt.where(Order.order_time >= datetime.combine(date_from, time.min))
    if date_to:
        stmt = stmt.where(Order.order_time <= datetime.combine(date_to, time.max))
    orders = list(db.scalars(stmt))

    order_count = len(orders)
    customer_count = len({o.user_id for o in orders})

    orders_by_status = {
        "received": 0,
        "processing": 0,
        "shipping": 0,
        "closed": 0,
        "cancelled": 0,
        "returned": 0,
    }
    for o in orders:
        if o.status in orders_by_status:
            orders_by_status[o.status] += 1

    sales_total = Decimal(0)
    for o in orders:
        if o.status in ("cancelled", "returned"):
            continue
        order_net = sum((it.unit_price * it.quantity - it.event_discount for it in o.items), Decimal(0))
        store_items: dict[int, Decimal] = {}
        for it in o.items:
            sid = it.product.store_id
            net = it.unit_price * it.quantity - it.event_discount
            store_items[sid] = store_items.get(sid, Decimal(0)) + net

        for sid, s_net in store_items.items():
            if store_id is not None and sid != store_id:
                continue
            share = round_half_up(Decimal(o.total) * s_net / order_net) if order_net > 0 else Decimal(0)
            sales_total += share

        if o.return_request is not None and o.return_request.status == "approved" and o.status != "returned":
            for ri in o.return_request.items:
                if (ri.refund_amount is not None and (store_id is None or
                        any(it.item_no == ri.item_no and it.product.store_id == store_id for it in o.items))):
                    sales_total -= Decimal(ri.refund_amount)

    pending_stmt = select(func.count(ReturnRequest.return_id)).where(ReturnRequest.status == "pending")
    if store_id is not None:
        pending_stmt = pending_stmt.where(ReturnRequest.order_id.in_(deps.store_order_ids(store_id)))
    if date_from:
        pending_stmt = pending_stmt.where(func.date(ReturnRequest.requested_at) >= date_from)
    if date_to:
        pending_stmt = pending_stmt.where(func.date(ReturnRequest.requested_at) <= date_to)
    pending_returns = db.scalar(pending_stmt) or 0

    return {
        "order_count": order_count,
        "sales_total": int(sales_total),
        "customer_count": customer_count,
        "pending_returns": pending_returns,
        "orders_by_status": orders_by_status,
    }
