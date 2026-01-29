"""游客与注册用户用量：剩余次数、扣减。"""
from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from sqlalchemy.orm import Session

from src.config import get_settings
from src.db.models import User, GuestUsage


@dataclass
class GuestIdentity:
    type: Literal["guest"] = "guest"
    guest_id: str = ""


@dataclass
class UserIdentity:
    type: Literal["user"] = "user"
    user_id: int = 0
    email: str = ""
    role: str = "user"
    balance: int = 0


def get_or_create_guest(db: Session, guest_id: str | None) -> tuple[GuestIdentity, int]:
    """返回 (identity, remaining)。若 guest_id 为空则创建新游客并写入 DB。"""
    settings = get_settings().auth
    quota = settings.guest_free_quota
    if not guest_id or not guest_id.strip():
        guest_id = str(uuid4())
        row = GuestUsage(guest_id=guest_id, count=0)
        db.add(row)
        db.commit()
        return GuestIdentity(guest_id=guest_id), quota
    row = db.query(GuestUsage).filter(GuestUsage.guest_id == guest_id).first()
    if not row:
        row = GuestUsage(guest_id=guest_id, count=0)
        db.add(row)
        db.commit()
    remaining = max(0, quota - row.count)
    return GuestIdentity(guest_id=guest_id), remaining


def get_guest_remaining(db: Session, guest_id: str) -> int:
    settings = get_settings().auth
    row = db.query(GuestUsage).filter(GuestUsage.guest_id == guest_id).first()
    if not row:
        return settings.guest_free_quota
    return max(0, settings.guest_free_quota - row.count)


def consume_guest(db: Session, guest_id: str) -> None:
    row = db.query(GuestUsage).filter(GuestUsage.guest_id == guest_id).first()
    if not row:
        return
    row.count += 1
    db.commit()


def get_user_identity_and_remaining(db: Session, user_id: int) -> tuple[UserIdentity | None, int]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None, 0
    identity = UserIdentity(
        user_id=user.id,
        email=user.email,
        role=user.role,
        balance=user.balance,
    )
    if user.role == "admin":
        remaining = 999999  # 管理员不限
    else:
        remaining = max(0, user.balance)
    return identity, remaining


def consume_user(db: Session, user_id: int) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role == "admin":
        return
    user.balance = max(0, user.balance - 1)
    db.commit()
