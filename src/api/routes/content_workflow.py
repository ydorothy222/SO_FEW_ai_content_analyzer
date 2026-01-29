"""
AI 内容永动机工作流 API。
顺序：拆解(Skill1) → 想清楚(Skill2) → 写一次(Skill3) → 用到极致(Skill4)
需登录或游客身份，且剩余用量 > 0；每次运行扣减 1 次。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.deps import require_quota
from src.db import get_db
from src.services.content_skills_service import (
    skill1_content_structure_judge,
    skill2_pre_writing_clarifier,
    skill3_mother_content_architect,
    skill4_content_repurposing_engine,
)
from src.services.usage_service import consume_guest, consume_user


router = APIRouter(prefix="/content-workflow", tags=["content-workflow"])


# --- Request/Response models ---


class Skill1Request(BaseModel):
    content: str = Field(..., description="一条完整内容（文章/帖子/视频脚本/转写文本）")


class Skill2Request(BaseModel):
    writing_intent: str = Field(default="", description="模糊写作意图，可留空")


class Skill3Request(BaseModel):
    core_idea: str = Field(..., description="已被验证有效的核心观点")


class Skill4Request(BaseModel):
    mother_content: str = Field(..., description="一篇完整母内容")


# --- Endpoints ---


def _consume_after_skill(db: Session, identity_info: dict) -> None:
    identity = identity_info.get("identity")
    if not identity:
        return
    if getattr(identity, "type", None) == "guest":
        consume_guest(db, getattr(identity, "guest_id", "") or "")
    elif getattr(identity, "type", None) == "user" and getattr(identity, "role", "") != "admin":
        consume_user(db, getattr(identity, "user_id", 0) or 0)


@router.post("/skill/1", summary="爆款结构拆解器")
def run_skill1(
    body: Skill1Request,
    db: Session = Depends(get_db),
    identity_info: dict = Depends(require_quota),
) -> dict:
    """判断内容结构是否值得复用。每次运行扣减 1 次用量。"""
    try:
        result = skill1_content_structure_judge(body.content)
        _consume_after_skill(db, identity_info)
        return {"ok": True, "skill_id": 1, "skill_name": "爆款结构拆解器", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill/2", summary="写作前元思考澄清器")
def run_skill2(
    body: Skill2Request,
    db: Session = Depends(get_db),
    identity_info: dict = Depends(require_quota),
) -> dict:
    """输出 6 个写作前必须回答的澄清问题。每次运行扣减 1 次用量。"""
    try:
        result = skill2_pre_writing_clarifier(body.writing_intent)
        _consume_after_skill(db, identity_info)
        return {"ok": True, "skill_id": 2, "skill_name": "写作前元思考澄清器", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill/3", summary="母内容结构构建器")
def run_skill3(
    body: Skill3Request,
    db: Session = Depends(get_db),
    identity_info: dict = Depends(require_quota),
) -> dict:
    """基于核心观点，输出母内容的完整结构蓝图。每次运行扣减 1 次用量。"""
    try:
        result = skill3_mother_content_architect(body.core_idea)
        _consume_after_skill(db, identity_info)
        return {"ok": True, "skill_id": 3, "skill_name": "母内容结构构建器", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill/4", summary="内容裂变与复利引擎")
def run_skill4(
    body: Skill4Request,
    db: Session = Depends(get_db),
    identity_info: dict = Depends(require_quota),
) -> dict:
    """将母内容裂变为多平台、多形式可分发内容。每次运行扣减 1 次用量。"""
    try:
        result = skill4_content_repurposing_engine(body.mother_content)
        _consume_after_skill(db, identity_info)
        return {"ok": True, "skill_id": 4, "skill_name": "内容裂变与复利引擎", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deduct-one", summary="[测试] 仅扣减 1 次用量，不调用 LLM")
def deduct_one(
    db: Session = Depends(get_db),
    identity_info: dict = Depends(require_quota),
) -> dict:
    """仅用于验证次数控制逻辑，不消耗 DashScope。"""
    _consume_after_skill(db, identity_info)
    return {"ok": True, "message": "已扣减 1 次"}


@router.get("/workflow", summary="工作流说明")
def get_workflow() -> dict:
    """返回四步工作流顺序与各 Skill 说明，供前端展示。"""
    return {
        "order": "拆解 → 想清楚 → 写一次 → 用到极致",
        "steps": [
            {
                "skill_id": 1,
                "name": "爆款结构拆解器",
                "short": "拆解",
                "description": "判断内容结构是否值得复用；只分析结构，不改写。",
                "input_hint": "粘贴高赞/高转发内容（文章、帖子、视频脚本等）",
            },
            {
                "skill_id": 2,
                "name": "写作前元思考澄清器",
                "short": "想清楚",
                "description": "写作前强制澄清：目标读者、平台、痛点、结论、证据、风格。",
                "input_hint": "可留空或写模糊写作意图",
            },
            {
                "skill_id": 3,
                "name": "母内容结构构建器",
                "short": "写一次",
                "description": "把已验证观点升级为一篇母内容的结构蓝图（承诺、钩子、正文结构、CTA、裂变方向）。",
                "input_hint": "输入核心观点或已验证的想法",
            },
            {
                "skill_id": 4,
                "name": "内容裂变与复利引擎",
                "short": "用到极致",
                "description": "把一份母内容裂变为短内容、钩子、平台结构、视频脚本、CTA 备选。",
                "input_hint": "粘贴完整母内容（长文/视频稿/Newsletter 等）",
            },
        ],
    }
