"""注册、登录、JWT 签发与校验。"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import get_settings
from src.db.models import User

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(user_id: int, email: str, role: str) -> str:
    settings = get_settings().auth
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> Optional[dict]:
    try:
        settings = get_settings().auth
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception:
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def register_user(db: Session, email: str, password: str) -> User:
    if get_user_by_email(db, email):
        raise ValueError("该邮箱已注册")
    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role="user",
        balance=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> User:
    settings = get_settings().auth
    # 管理员账号：账号密码均为 YANGRONG（或配置值）
    if email.strip().upper() == settings.admin_username.upper() and password == settings.admin_password:
        admin = get_user_by_email(db, settings.admin_username.upper())
        if not admin:
            admin = User(
                email=settings.admin_username.upper(),
                password_hash=hash_password(settings.admin_password),
                role="admin",
                balance=0,  # 管理员不扣余额
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        return admin
    user = get_user_by_email(db, email.strip().lower())
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("邮箱或密码错误")
    return user
