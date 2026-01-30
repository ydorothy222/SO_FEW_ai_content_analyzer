"""注册、登录、登出、当前身份与用量。"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.api.deps import get_identity_optional
from src.db import get_db
from src.services.auth_service import (
    create_access_token,
    login_user,
    register_user,
)
from src.services.email_service import send_welcome_email
from src.services.usage_service import get_or_create_guest
from src.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie 配置
COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 天
COOKIE_PATH = "/"
COOKIE_SAMESITE = "lax"
COOKIE_HTTPONLY = True


class RegisterBody(BaseModel):
    email: str = Field(..., min_length=3, max_length=256)
    password: str = Field(...)

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or v.count("@") != 1:
            raise ValueError("请输入有效邮箱")
        return v


class LoginBody(BaseModel):
    email: str = Field(..., description="邮箱或账号")
    password: str = Field(...)


@router.post("/register")
def register(
    body: RegisterBody,
    response: Response,
    db: Session = Depends(get_db),
):
    """邮箱注册，注册后余额为 0，需充值后使用。若配置了 SMTP 且开启欢迎邮件，会发一封欢迎邮件。"""
    try:
        user = register_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if get_settings().email.send_welcome_email:
        try:
            send_welcome_email(user.email, body.email.split("@")[0])
        except Exception:
            pass
    token = create_access_token(user.id, user.email, user.role)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=COOKIE_MAX_AGE,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        httponly=COOKIE_HTTPONLY,
    )
    response.delete_cookie(key="guest_id", path=COOKIE_PATH)
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "balance": user.balance,
        },
        "message": "注册成功，请前往「充值」获取使用次数",
    }


@router.post("/login")
def login(
    body: LoginBody,
    response: Response,
    db: Session = Depends(get_db),
):
    """登录。管理员账号免费用量，普通用户用邮箱+密码。"""
    try:
        user = login_user(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    token = create_access_token(user.id, user.email, user.role)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=COOKIE_MAX_AGE,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        httponly=COOKIE_HTTPONLY,
    )
    response.delete_cookie(key="guest_id", path=COOKIE_PATH)
    remaining = "不限" if user.role == "admin" else user.balance
    return {
        "ok": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "balance": user.balance,
        },
        "remaining": remaining,
    }


@router.post("/logout")
def logout(response: Response):
    """清除登录态。"""
    response.delete_cookie(key="access_token", path=COOKIE_PATH)
    return {"ok": True}


@router.get("/me")
def me(
    response: Response,
    db: Session = Depends(get_db),
    identity_info=Depends(get_identity_optional),
):
    """
    当前身份与剩余用量。
    若未带任何 Cookie，会创建新游客并 Set-Cookie(guest_id)，返回游客剩余次数。
    """
    if identity_info is not None:
        identity = identity_info["identity"]
        remaining = identity_info["remaining"]
        if hasattr(identity, "type"):
            if identity.type == "guest":
                return {
                    "type": "guest",
                    "guest_id": identity.guest_id,
                    "remaining": remaining,
                    "message": "游客体验，共 3 次免费；用完后请注册并充值",
                }
            if identity.type == "user":
                return {
                    "type": "user",
                    "user_id": identity.user_id,
                    "email": identity.email,
                    "role": identity.role,
                    "balance": identity.balance,
                    "remaining": remaining,
                }
    # 无 Cookie：初始化游客
    guest_identity, remaining = get_or_create_guest(db, None)
    response.set_cookie(
        key="guest_id",
        value=guest_identity.guest_id,
        max_age=COOKIE_MAX_AGE,
        path=COOKIE_PATH,
        samesite=COOKIE_SAMESITE,
        httponly=COOKIE_HTTPONLY,
    )
    return {
        "type": "guest",
        "guest_id": guest_identity.guest_id,
        "remaining": remaining,
        "message": "游客体验，共 3 次免费；用完后请注册并充值",
    }
