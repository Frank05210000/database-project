"""登入與角色授權（AAS-F-003、BR-21）。

每次請求都從資料庫重新讀取使用者與角色，所以管理員停用帳號或移除角色會立即生效。
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_optional_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer),
                      db: Session = Depends(get_db)) -> User | None:
    if cred is None:
        return None
    user_id = decode_token(cred.credentials)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登入已失效，請重新登入")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "帳號不存在或已停用")
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "請先登入")
    return user


def require_role(role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if not user.has_role(role):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"BR-21：此功能需要 {role} 角色")
        return user
    return checker


require_customer = require_role("customer")
require_staff = require_role("staff")
require_admin = require_role("admin")
