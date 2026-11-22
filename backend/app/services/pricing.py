"""訂單金額計算（BR-09～BR-17、DMS-F-009）。購物車預覽與結帳共用同一套計算。

計算順序（BR-10）：
  1. 各商品小計 = 單價 × 數量
  2. 扣除特殊活動折扣（商品層級，折扣率或買 X 送 Y）
  3. 以扣除後金額計算季節性折扣（訂單層級，多筆依序連續疊加，BR-12）
  4. 以兩項折扣後的金額計算稅額（四捨五入至整數元），運費不課稅
  5. 兩項折扣後的金額達任一筆運費折扣門檻則免運費
訂單總額 = 小計 − 特殊活動折扣 − 季節性折扣 + 稅 + 運費 − 運費折扣（BR-09）

資料庫欄位對應：orders.shipping_fee 存基本運費，orders.discount_total 存三種折扣的合計，
所以 total = subtotal − discount_total + tax + shipping_fee。
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Discount, Product, ProductDiscount, SystemSetting


def round_half_up(x: Decimal) -> Decimal:
    return Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


@dataclass
class PricedLine:
    product_id: int
    product_name: str
    store_id: int
    unit_price: Decimal
    quantity: int
    event_discount: Decimal = Decimal(0)
    event_code: str | None = None
    event_description: str | None = None

    @property
    def line_subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

    @property
    def net_amount(self) -> Decimal:
        return self.line_subtotal - self.event_discount


@dataclass
class AppliedDiscount:
    discount_code: str
    discount_type: str
    description: str
    amount: Decimal


@dataclass
class PriceQuote:
    lines: list[PricedLine]
    subtotal: Decimal
    event_discount: Decimal
    seasonal_discount: Decimal
    tax_base: Decimal
    tax: Decimal
    shipping_fee: Decimal
    shipping_discount: Decimal
    discount_total: Decimal
    total: Decimal
    tax_rate: Decimal
    applied: list[AppliedDiscount] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "lines": [{
                "product_id": l.product_id, "product_name": l.product_name, "store_id": l.store_id,
                "unit_price": int(l.unit_price), "quantity": l.quantity, "line_subtotal": int(l.line_subtotal),
                "event_discount": int(l.event_discount), "event_code": l.event_code,
                "event_description": l.event_description, "net_amount": int(l.net_amount),
            } for l in self.lines],
            "subtotal": int(self.subtotal),
            "event_discount": int(self.event_discount),
            "seasonal_discount": int(self.seasonal_discount),
            "tax_base": int(self.tax_base),
            "tax_rate": float(self.tax_rate),
            "tax": int(self.tax),
            "shipping_fee": int(self.shipping_fee),
            "shipping_discount": int(self.shipping_discount),
            "discount_total": int(self.discount_total),
            "total": int(self.total),
            "applied_discounts": [{
                "discount_code": a.discount_code, "discount_type": a.discount_type,
                "description": a.description, "amount": int(a.amount)} for a in self.applied],
        }


def get_setting(db: Session, key: str, default: str) -> str:
    row = db.get(SystemSetting, key)
    return row.setting_value if row else default


def active_discounts(db: Session, on: date, dtype: str) -> list[Discount]:
    """有效期間內（含首尾兩日，BR-14）且啟用中的折扣，依代碼排序。"""
    return list(db.scalars(
        select(Discount).where(Discount.discount_type == dtype, Discount.is_active.is_(True),
                               Discount.start_date <= on, Discount.end_date >= on)
        .order_by(Discount.discount_code)))


def event_discount_for(db: Session, product_id: int, on: date) -> Discount | None:
    """商品目前適用的特殊活動折扣（BR-13 保證同一天最多一筆）。"""
    return db.scalar(
        select(Discount).join(ProductDiscount, ProductDiscount.discount_code == Discount.discount_code)
        .where(ProductDiscount.product_id == product_id, Discount.is_active.is_(True),
               Discount.start_date <= on, Discount.end_date >= on))


def event_discounts_for(db: Session, product_ids: list[int], on: date) -> dict[int, Discount]:
    """一次查出多項商品目前適用的特殊活動折扣，避免商品列表逐筆查詢（N+1）。"""
    if not product_ids:
        return {}
    rows = db.execute(
        select(ProductDiscount.product_id, Discount)
        .join(Discount, ProductDiscount.discount_code == Discount.discount_code)
        .where(ProductDiscount.product_id.in_(product_ids), Discount.is_active.is_(True),
               Discount.start_date <= on, Discount.end_date >= on))
    return {pid: d for pid, d in rows}


def event_amount(d: Discount, unit_price: Decimal, qty: int) -> Decimal:
    line = unit_price * qty
    if d.rate is not None:
        return round_half_up(line * d.rate)
    # BR-16：每購買 X+Y 件只需支付 X 件
    group = d.buy_qty + d.free_qty
    return Decimal((qty // group) * d.free_qty) * unit_price


def quote(db: Session, items: list[tuple[Product, int]], on: date) -> PriceQuote:
    """items 為 (商品, 數量)；回傳完整金額明細。不檢查庫存，由呼叫端處理。"""
    tax_rate = Decimal(get_setting(db, "tax_rate", "0.05"))
    base_shipping = Decimal(get_setting(db, "shipping_fee", "100"))

    lines: list[PricedLine] = []
    event_by_code: dict[str, AppliedDiscount] = {}
    for product, qty in items:
        line = PricedLine(product.product_id, product.name, product.store_id, Decimal(product.price), qty)
        d = event_discount_for(db, product.product_id, on)
        if d is not None:
            line.event_discount = event_amount(d, line.unit_price, qty)
            line.event_code, line.event_description = d.discount_code, d.description
            if line.event_discount > 0:
                ad = event_by_code.setdefault(
                    d.discount_code, AppliedDiscount(d.discount_code, d.discount_type, d.description, Decimal(0)))
                ad.amount += line.event_discount
        lines.append(line)

    subtotal = sum((l.line_subtotal for l in lines), Decimal(0))
    event_total = sum((l.event_discount for l in lines), Decimal(0))
    applied = list(event_by_code.values())

    # BR-12：季節性折扣依序連續疊加
    amount = subtotal - event_total
    seasonal_total = Decimal(0)
    for d in active_discounts(db, on, "seasonal"):
        cut = round_half_up(amount * d.rate)
        if cut > 0:
            applied.append(AppliedDiscount(d.discount_code, d.discount_type, d.description, cut))
        amount -= cut
        seasonal_total += cut

    tax = round_half_up(amount * tax_rate)

    # BR-12：達任一筆運費折扣門檻即免運；記錄門檻最低的那一筆
    shipping_discount = Decimal(0)
    if lines:
        qualified = [d for d in active_discounts(db, on, "shipping") if amount >= d.min_amount]
        if qualified:
            d = min(qualified, key=lambda x: (x.min_amount, x.discount_code))
            shipping_discount = base_shipping
            applied.append(AppliedDiscount(d.discount_code, d.discount_type, d.description, base_shipping))
    shipping_fee = base_shipping if lines else Decimal(0)

    discount_total = event_total + seasonal_total + shipping_discount
    total = subtotal - discount_total + tax + shipping_fee
    return PriceQuote(lines, subtotal, event_total, seasonal_total, amount, tax, shipping_fee,
                      shipping_discount, discount_total, total, tax_rate, applied)
