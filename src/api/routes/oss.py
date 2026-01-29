from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from src.db import get_db
from src.services.recording_service import RecordingService

from src.services.oss_service import get_oss_service


router = APIRouter(prefix="/oss", tags=["oss"])


@router.post("/upload-url")
def get_upload_url(
    recording_id: str = Query(..., description="录音 ID，用于生成唯一对象名"),
    ext: str = Query("wav", description="文件扩展名（如 wav/m4a/mp3），用于生成对象名"),
):
    if not recording_id:
        raise HTTPException(status_code=400, detail="recording_id is required")
    oss_service = get_oss_service()
    key = oss_service.object_key_for_recording_with_ext(recording_id, ext)
    url = oss_service.sign_url_for_key("PUT", key, 600)
    return {"data": {"recording_id": recording_id, "object_key": key, "upload_url": url}}


@router.get("/download-url/{recording_id}")
def get_download_url(recording_id: str, db: Session = Depends(get_db)):
    if not recording_id:
        raise HTTPException(status_code=400, detail="recording_id is required")
    oss_service = get_oss_service()
    rec = RecordingService(db).get_recording(recording_id)
    object_key = rec.oss_file_path if rec else oss_service.object_key_for_recording(recording_id)
    url = oss_service.sign_url_for_key("GET", object_key, 3600)
    return {"data": {"recording_id": recording_id, "object_key": object_key, "download_url": url}}


