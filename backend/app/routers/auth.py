"""AAS：註冊、登入、個人資料（AAS-F-001～AAS-F-004、BR-01）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User, UserRole
from app.schemas_w1 import Address, Email, LoginId, Name, Password, Phone, ProfileIn, UserOut, user_out
from app.security import create_token, hash_password, verify_password

router = APIRouter()


class RegisterIn(BaseModel):
    loginid: LoginId
    name: Name
    password: Password
    email: Email
    address: Address
    phone: Phone = None


class LoginIn(BaseModel):
    loginid: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PasswordIn(BaseModel):
    old_password: str
    new_password: Password


def ensure_loginid_free(db: Session, loginid: str) -> None:
    if db.scalar(select(User.user_id).where(User.loginid == loginid)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "BR-01：loginid 已被使用")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    ensure_loginid_free(db, body.loginid)
    user = User(loginid=body.loginid, name=body.name, password_hash=hash_password(body.password),
                email=body.email, address=body.address, phone=body.phone, is_active=True)
    user.role_rows.append(UserRole(role="customer"))
    db.add(user)
    db.commit()   # 同時註冊的競爭情況由 UNIQUE(loginid) 擋下，errors.py 轉成 409
    db.refresh(user)
    return user_out(user)


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.loginid == body.loginid))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "帳號或密碼錯誤")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "帳號已停用")
    return LoginOut(access_token=create_token(user.user_id), user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)


@router.put("/me", response_model=UserOut)
def update_me(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.name, user.email, user.address, user.phone = body.name, body.email, body.address, body.phone
    db.commit()
    return user_out(user)


@router.put("/me/password")
def change_password(body: PasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "舊密碼不正確")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
