from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db import get_db, Base, engine
from src.services.asr_service import get_asr_service
from src.services.oss_service import get_oss_service
from src.services.recording_service import RecordingService
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.analysis_repo import AnalysisRepo
from src.services.llm_service import get_llm_service


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class FullTestRequest(BaseModel):
    recording_id: str = Field(..., description="已上传到 OSS 的录音 ID")
    question: str = Field(..., description="要提给助手的问题")


@router.post("/full-test")
def full_test(body: FullTestRequest, db: Session = Depends(get_db)):
    """
    一键从录音 -> 转写 -> 分析 -> 问答，用于 MVP 联调测试。
    前置条件：该 recording_id 对应的音频文件已通过 /v1/oss/upload-url 上传到 OSS。
    """
    recording_service = RecordingService(db)
    rec = recording_service.get_recording(body.recording_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    # 1) 生成 DashScope 可访问的下载 URL，提交转写任务并等待完成
    oss = get_oss_service()
    download_url = oss.sign_url_for_key("GET", rec.oss_file_path, 3600)

    asr = get_asr_service()
    task_id = asr.create_transcription_task([download_url])
    try:
        segments = asr.wait_transcription(task_id, max_wait_seconds=600)
    except (TimeoutError, RuntimeError) as e:
        rec.status = "failed"
        rec.error_code = "ASR_ERROR"
        rec.error_message = f"ASR wait failed: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"ASR failed: {str(e)}")
    
    if not segments:
        rec.status = "failed"
        rec.error_code = "ASR_EMPTY"
        rec.error_message = "ASR returned empty segments after successful wait"
        db.commit()
        raise HTTPException(status_code=500, detail="ASR failed or returned empty result")

    transcript_service = TranscriptService(db)
    transcript_service.replace_segments(body.recording_id, segments, asr_model=asr.settings.asr_model)

    # 2) 分析
    payload = [
        {"segment_index": i, "start_ms": s.get("start_ms", 0), "end_ms": s.get("end_ms", 0), "text": s.get("text", "")}
        for i, s in enumerate(segments)
    ]
    analysis_dict = AnalysisService().analyze_transcript(payload)
    analysis_repo = AnalysisRepo(db)
    analysis_repo.upsert_analysis(body.recording_id, analysis_dict, version="v1")

    rec.status = "ready"
    db.commit()

    # 3) 问答（只基于当前 recording_id）
    merged: List[str] = []
    seg_db = transcript_service.list_segments(body.recording_id)
    for s in seg_db:
        merged.append(f"[{body.recording_id}#{s.segment_index}] {s.text}")

    llm = get_llm_service()
    prompt = (
        "你是一个严谨的中文智能陪伴助理。以下是用户的一段对话转写片段：\n"
        + "\n".join(merged)
        + "\n\n用户问题："
        + body.question
        + "\n\n请结合对话内容认真回答，不要编造不存在的内容。"
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

    return {
        "data": {
            "recording_id": body.recording_id,
            "status": rec.status,
            "segments_saved": len(segments),
            "analysis_version": "v1",
            "answer": answer,
        }
    }


