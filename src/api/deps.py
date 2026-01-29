"""公共依赖：从 Cookie 解析身份与用量。"""
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.db import get_db
from src.services.auth_service import decode_access_token
from src.services.usage_service import (
    GuestIdentity,
    UserIdentity,
    get_or_create_guest,
    get_guest_remaining,
    get_user_identity_and_remaining,
)


def get_identity(
    request: Request,
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias="access_token"),
    guest_id: str | None = Cookie(default=None, alias="guest_id"),
):
    """
    从 Cookie 解析身份：优先 access_token（已登录），否则 guest_id（游客）。
    若为游客且未带 guest_id，不在此处创建（由 GET /auth/me 负责创建并 Set-Cookie）。
    """
    if access_token:
        payload = decode_access_token(access_token)
        if payload and payload.get("sub"):
            try:
                uid = int(payload["sub"])
            except (ValueError, TypeError):
                pass
            else:
                identity, remaining = get_user_identity_and_remaining(db, uid)
                if identity is not None:
                    return {"identity": identity, "remaining": remaining}
    if guest_id and guest_id.strip():
        remaining = get_guest_remaining(db, guest_id)
        return {"identity": GuestIdentity(guest_id=guest_id), "remaining": remaining}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="请先访问首页以初始化，或登录后再使用",
    )


def get_identity_optional(
    request: Request,
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias="access_token"),
    guest_id: str | None = Cookie(default=None, alias="guest_id"),
):
    """可选身份：用于 /auth/me，未登录时可为游客或需初始化。"""
    if access_token:
        payload = decode_access_token(access_token)
        if payload and payload.get("sub"):
            try:
                uid = int(payload["sub"])
            except (ValueError, TypeError):
                pass
            else:
                identity, remaining = get_user_identity_and_remaining(db, uid)
                if identity is not None:
                    return {"identity": identity, "remaining": remaining}
    if guest_id and guest_id.strip():
        remaining = get_guest_remaining(db, guest_id)
        return {"identity": GuestIdentity(guest_id=guest_id), "remaining": remaining}
    return None


def require_quota(
    identity_info: dict = Depends(get_identity),
):
    """要求有剩余用量（游客≤3 次或用户余额>0 或管理员）。"""
    remaining = identity_info.get("remaining", 0)
    if remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="免费次数已用完，请注册并充值后继续使用",
        )
    return identity_info
