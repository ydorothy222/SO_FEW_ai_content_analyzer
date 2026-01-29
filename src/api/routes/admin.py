"""管理员：充值（为指定用户增加余额）。"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.deps import get_identity
from src.db import get_db
from src.db.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(identity_info: dict = Depends(get_identity)):
    identity = identity_info.get("identity")
    if not identity or not getattr(identity, "role", None) == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")
    return identity_info


class AddBalanceBody(BaseModel):
    user_id: int = Field(..., description="要充值的用户 ID")
    amount: int = Field(..., gt=0, description="增加次数，正整数")


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """列出所有用户（id、email、balance），供管理员充值选择。"""
    users = db.query(User).order_by(User.id).all()
    return {
        "users": [
            {"id": u.id, "email": u.email, "role": u.role, "balance": u.balance or 0}
            for u in users
        ],
    }


@router.post("/add-balance")
def add_balance(
    body: AddBalanceBody,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """为指定用户增加可用次数（仅管理员）。"""
    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.balance = (user.balance or 0) + body.amount
    db.commit()
    db.refresh(user)
    return {"ok": True, "user_id": user.id, "new_balance": user.balance}
