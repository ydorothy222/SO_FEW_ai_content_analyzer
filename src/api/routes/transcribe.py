from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db import get_db, Base, engine
from src.services.asr_service import get_asr_service
from src.services.oss_service import get_oss_service
from src.services.recording_service import RecordingService
from src.services.transcript_service import TranscriptService


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/transcribe", tags=["transcribe"])


class TranscribeStartRequest(BaseModel):
    recording_id: str
    use_callback: bool = False


@router.post("/start")
def start_transcribe(body: TranscribeStartRequest, db: Session = Depends(get_db)):
    recording_service = RecordingService(db)
    rec = recording_service.get_recording(body.recording_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    oss = get_oss_service()
    download_url = oss.sign_url_for_key("GET", rec.oss_file_path, 3600)

    asr = get_asr_service()
    task_id = asr.create_transcription_task([download_url])

    rec.status = "transcribing"
    db.commit()

    return {"data": {"recording_id": body.recording_id, "task_id": task_id, "status": "transcribing"}}


@router.get("/query/{task_id}")
def query_transcribe(task_id: str):
    asr = get_asr_service()
    output = asr.fetch_task(task_id)
    return {"data": {"task_id": task_id, "output": output}}


class TranscribeWaitRequest(BaseModel):
    recording_id: str
    task_id: str


@router.post("/wait-and-save")
def wait_and_save(body: TranscribeWaitRequest, db: Session = Depends(get_db)):
    recording_service = RecordingService(db)
    rec = recording_service.get_recording(body.recording_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    asr = get_asr_service()
    segments = asr.wait_transcription(body.task_id)
    if not segments:
        rec.status = "failed"
        rec.error_code = "ASR_EMPTY"
        rec.error_message = "ASR returned empty segments"
        db.commit()
        raise HTTPException(status_code=500, detail="ASR failed or returned empty result")

    transcript_service = TranscriptService(db)
    transcript_service.replace_segments(body.recording_id, segments, asr_model=asr.settings.asr_model)

    rec.status = "analyzing"
    db.commit()

    return {"data": {"recording_id": body.recording_id, "segments_saved": len(segments), "status": rec.status}}


