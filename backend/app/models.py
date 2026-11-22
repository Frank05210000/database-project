"""SQLAlchemy ORM 對應 db/init/01_schema.sql 的 15 張表。

資料表由 SQL 檔建立（含 CHECK、EXCLUDE、trigger），這裡只做對應，不用 create_all。
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (Boolean, Date, ForeignKey, ForeignKeyConstraint, Integer, Numeric, SmallInteger,
                        String, Text, DateTime, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loginid: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    role_rows: Mapped[list["UserRole"]] = relationship(cascade="all, delete-orphan", lazy="selectin")

    @property
    def roles(self) -> list[str]:
        order = {"customer": 0, "staff": 1, "admin": 2}
        return sorted((r.role for r in self.role_rows), key=lambda r: order.get(r, 9))

    def has_role(self, role: str) -> bool:
        return any(r.role == role for r in self.role_rows)


class UserRole(Base):
    __tablename__ = "user_role"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(10), primary_key=True)


class Store(Base):
    __tablename__ = "store"
    store_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    address: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))


class Product(Base):
    __tablename__ = "product"
    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.store_id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(30))
    image_url: Mapped[str | None] = mapped_column(String(300))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    stock: Mapped[int] = mapped_column(Integer)
    is_listed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped[Store] = relationship(lazy="joined", innerjoin=True)


class CartItem(Base):
    __tablename__ = "cart_item"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped[Product] = relationship(lazy="joined")


class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    order_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    recipient_name: Mapped[str] = mapped_column(String(50))
    recipient_phone: Mapped[str] = mapped_column(String(20))
    recipient_address: Mapped[str] = mapped_column(String(200))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(10, 0), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    status: Mapped[str] = mapped_column(String(10), default="received")
    paid_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[User] = relationship(lazy="joined")
    items: Mapped[list["OrderItem"]] = relationship(
        cascade="all, delete-orphan", order_by="OrderItem.item_no", lazy="selectin")
    history: Mapped[list["OrderStatusHistory"]] = relationship(
        order_by="OrderStatusHistory.seq_no", lazy="selectin", viewonly=True)
    discounts: Mapped[list["OrderDiscount"]] = relationship(cascade="all, delete-orphan", lazy="selectin")
    return_request: Mapped["ReturnRequest | None"] = relationship(
        back_populates="order", uselist=False, lazy="selectin", viewonly=True)


class OrderItem(Base):
    __tablename__ = "order_item"
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), primary_key=True)
    item_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"))
    product_name: Mapped[str] = mapped_column(String(100))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 0))
    quantity: Mapped[int] = mapped_column(Integer)
    event_discount: Mapped[Decimal] = mapped_column(Numeric(10, 0), default=0)

    product: Mapped[Product] = relationship(lazy="joined")

    @property
    def line_subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), primary_key=True)
    seq_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    status: Mapped[str] = mapped_column(String(10))
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    changed_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"))

    changer: Mapped[User] = relationship(lazy="joined")


class Discount(Base):
    __tablename__ = "discount"
    discount_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    discount_type: Mapped[str] = mapped_column(String(15))
    description: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    rate: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 0))
    buy_qty: Mapped[int | None] = mapped_column(SmallInteger)
    free_qty: Mapped[int | None] = mapped_column(SmallInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    products: Mapped[list["ProductDiscount"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", passive_deletes=True)


class ProductDiscount(Base):
    __tablename__ = "product_discount"
    __table_args__ = (
        ForeignKeyConstraint(["discount_code", "discount_type", "start_date", "end_date"],
                             ["discount.discount_code", "discount.discount_type",
                              "discount.start_date", "discount.end_date"],
                             onupdate="CASCADE", ondelete="CASCADE"),
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id", ondelete="CASCADE"), primary_key=True)
    discount_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    discount_type: Mapped[str] = mapped_column(String(15), default="special_event")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    product: Mapped[Product] = relationship(lazy="joined")


class OrderDiscount(Base):
    __tablename__ = "order_discount"
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), primary_key=True)
    discount_code: Mapped[str] = mapped_column(ForeignKey("discount.discount_code"), primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 0))

    discount: Mapped[Discount] = relationship(lazy="joined")


class ReturnRequest(Base):
    __tablename__ = "return_request"
    return_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), unique=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    reason: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(10), default="pending")
    processed_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    reject_reason: Mapped[str | None] = mapped_column(String(300))
    refund_total: Mapped[Decimal | None] = mapped_column(Numeric(10, 0))

    order: Mapped[Order] = relationship(back_populates="return_request", lazy="joined")
    items: Mapped[list["ReturnItem"]] = relationship(
        cascade="all, delete-orphan", order_by="ReturnItem.item_no", lazy="selectin")


class ReturnItem(Base):
    __tablename__ = "return_item"
    __table_args__ = (
        ForeignKeyConstraint(["return_id", "order_id"],
                             ["return_request.return_id", "return_request.order_id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["order_id", "item_no"], ["order_item.order_id", "order_item.item_no"]),
    )
    return_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(Integer)
    item_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    return_qty: Mapped[int] = mapped_column(Integer)
    refund_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 0))


class StoreReview(Base):
    __tablename__ = "store_review"
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("store.store_id"), primary_key=True)
    rating: Mapped[int] = mapped_column(SmallInteger)
    comment: Mapped[str | None] = mapped_column(String(500))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped[Order] = relationship(lazy="joined")


class SystemSetting(Base):
    __tablename__ = "system_setting"
    setting_key: Mapped[str] = mapped_column(String(30), primary_key=True)
    setting_value: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(100))
