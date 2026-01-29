from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db import get_db, Base, engine
from src.services.recording_service import RecordingService
from src.services.transcript_service import TranscriptService
from src.services.llm_service import get_llm_service


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/qa", tags=["qa"])


class QARequest(BaseModel):
    recording_ids: List[str] = Field(..., description="需要纳入问答的录音 recording_id 列表")
    question: str


@router.post("")
def qa(body: QARequest, db: Session = Depends(get_db)):
    if not body.recording_ids:
        raise HTTPException(status_code=400, detail="recording_ids is required")

    recording_service = RecordingService(db)
    transcript_service = TranscriptService(db)

    merged: List[str] = []
    citations: List[dict] = []

    for rid in body.recording_ids:
        rec = recording_service.get_recording(rid)
        if not rec:
            continue
        segs = transcript_service.list_segments(rid)
        for s in segs:
            merged.append(f"[{rid}#{s.segment_index}] {s.text}")
            citations.append(
                {
                    "recording_id": rid,
                    "segment_index": s.segment_index,
                    "start_ms": s.start_ms,
                    "end_ms": s.end_ms,
                }
            )

    if not merged:
        raise HTTPException(status_code=400, detail="No transcript segments found for provided recording_ids")

    llm = get_llm_service()
    prompt = (
        "你是一个严谨的中文智能陪伴助理。以下是用户的对话转写片段（格式：[recording#segment] 文本）：\n"
        + "\n".join(merged)
        + "\n\n用户问题："
        + body.question
        + "\n\n要求：\n"
        + "1) 优先基于提供的内容回答，不要编造。\n"
        + "2) 如果涉及“见了哪些人”，请列出人物并给出对应片段编号作为证据。\n"
        + "3) 如果涉及“不妥当的地方”，指出片段编号并给出更合理的说法建议。\n"
        + "4) 输出：先给回答，再给 citations（列出你引用到的片段编号）。\n"
    )

    resp = llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    answer = resp.choices[0].message.content or ""

    return {"data": {"answer": answer, "available_citations": citations}}


