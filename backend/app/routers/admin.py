"""平台管理（依期中簡報）：管理員可新增、查詢、修改任何角色的帳號，整組指派角色，停用或啟用帳號。

系統至少保留一位啟用中的管理員：後端擋「停用自己」與「移除自己的 admin」，
資料庫的 deferred constraint trigger（trg_keep_one_admin）在 commit 時再檢查一次。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_admin
from app.models import Store, StoreStaff, User, UserRole
from app.routers.auth import ensure_loginid_free
from app.schemas_w1 import Address, Email, LoginId, Name, Password, Phone, Role, UserOut, user_out
from app.security import hash_password

router = APIRouter()


class UserCreateIn(BaseModel):
    loginid: LoginId
    name: Name
    password: Password
    email: Email
    address: Address = None
    phone: Phone = None
    store_id: int | None = None
    roles: list[Role] = Field(default_factory=lambda: ["customer"])


class UserUpdateIn(BaseModel):
    name: Name
    email: Email
    address: Address = None
    phone: Phone = None
    password: Password | None = None


class RolesIn(BaseModel):
    roles: list[Role]


class StoreIn(BaseModel):
    store_id: int | None


class StatusIn(BaseModel):
    is_active: bool


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到這位使用者")
    return user


def check_roles(roles: list[str]) -> set[str]:
    wanted = set(roles)
    if not wanted:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-02：每位使用者至少要有一個角色")
    return wanted


@router.get("/users", response_model=list[UserOut])
def list_users(q: str | None = None, role: Role | None = None, is_active: bool | None = None,
               db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stmt = select(User).order_by(User.user_id)
    if q:
        pat = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.loginid.ilike(pat), User.name.ilike(pat), User.email.ilike(pat)))
    if role:
        stmt = stmt.where(User.user_id.in_(select(UserRole.user_id).where(UserRole.role == role)))
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))
    return [user_out(u) for u in db.scalars(stmt)]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreateIn, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    roles = check_roles(body.roles)
    if body.store_id is not None:
        if "staff" not in roles:
            raise HTTPException(409, "BR-21：只有工作人員可以設定隸屬商店")
        if db.get(Store, body.store_id) is None:
            raise HTTPException(404, "找不到這間商店")
    ensure_loginid_free(db, body.loginid)
    user = User(loginid=body.loginid, name=body.name, password_hash=hash_password(body.password),
                email=body.email, address=body.address, phone=body.phone, is_active=True)
    user.role_rows.extend(UserRole(role=r) for r in sorted(roles))
    db.add(user)
    db.flush()  # 先建立角色，讓商店隸屬的 trigger 可以查到 staff
    if body.store_id is not None:
        db.add(StoreStaff(user_id=user.user_id, store_id=body.store_id))
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    def with_role(r: str) -> int:
        return db.scalar(select(func.count()).select_from(UserRole).where(UserRole.role == r)) or 0
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "customers": with_role("customer"),
        "staff": with_role("staff"),
        "admins": with_role("admin"),
        "inactive": db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(False))) or 0,
    }


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return user_out(get_user_or_404(db, user_id))


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdateIn, db: Session = Depends(get_db),
                _: User = Depends(require_admin)):
    user = get_user_or_404(db, user_id)
    user.name, user.email, user.address, user.phone = body.name, body.email, body.address, body.phone
    if body.password:
        user.password_hash = hash_password(body.password)
    db.commit()
    return user_out(user)


@router.put("/users/{user_id}/roles", response_model=UserOut)
def replace_roles(user_id: int, body: RolesIn, db: Session = Depends(get_db),
                  me: User = Depends(require_admin)):
    user = get_user_or_404(db, user_id)
    wanted = check_roles(body.roles)
    if user.user_id == me.user_id and "admin" not in wanted:
        raise HTTPException(status.HTTP_409_CONFLICT, "AAS：不能移除自己的平台管理員角色")
    # 只刪除與新增有差異的角色，避免同一主鍵先刪後插
    for row in [r for r in user.role_rows if r.role not in wanted]:
        user.role_rows.remove(row)
    current = {r.role for r in user.role_rows}
    user.role_rows.extend(UserRole(role=r) for r in sorted(wanted - current))
    db.commit()   # 若會讓系統沒有啟用中的管理員，trigger 在此拒絕 → 409
    db.refresh(user)
    return user_out(user)


@router.patch("/users/{user_id}/status", response_model=UserOut)
def set_status(user_id: int, body: StatusIn, db: Session = Depends(get_db), me: User = Depends(require_admin)):
    user = get_user_or_404(db, user_id)
    if user.user_id == me.user_id and not body.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "AAS：不能停用自己的帳號")
    user.is_active = body.is_active
    db.commit()
    return user_out(user)


@router.put("/users/{user_id}/store", response_model=UserOut)
def set_store(user_id: int, body: StoreIn, db: Session = Depends(get_db),
              _: User = Depends(require_admin)):
    user = get_user_or_404(db, user_id)
    if not user.has_role("staff"):
        raise HTTPException(409, "BR-21：只有工作人員可以設定隸屬商店")
    if body.store_id is not None and db.get(Store, body.store_id) is None:
        raise HTTPException(404, "找不到這間商店")
    row = db.get(StoreStaff, user_id)
    if body.store_id is None:
        if row is not None:
            db.delete(row)
    elif row is None:
        db.add(StoreStaff(user_id=user_id, store_id=body.store_id))
    else:
        row.store_id = body.store_id
    db.commit()
    db.refresh(user)
    return user_out(user)
