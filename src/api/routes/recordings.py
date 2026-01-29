from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.db import get_db, Base, engine
from src.services.recording_service import RecordingService
from src.services.oss_service import get_oss_service


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/recordings", tags=["recordings"])


class RecordingCreateRequest(BaseModel):
    device_id: str = Field(..., description="ESP32-C3 MAC 地址")
    recording_id: str = Field(..., description="幂等 ID，如 deviceId_startTs")
    start_at: int = Field(..., description="录音开始 Unix 时间戳（秒）")
    end_at: int = Field(..., description="录音结束 Unix 时间戳（秒）")
    timezone: str = Field("Asia/Shanghai", description="时区，默认 Asia/Shanghai")
    file_ext: str = Field("wav", description="文件扩展名（wav/m4a/mp3...），用于 OSS 对象名")


class RecordingResponse(BaseModel):
    device_id: str
    recording_id: str
    start_at: int
    end_at: int
    timezone: str
    oss_file_path: str
    status: str


@router.post("", response_model=RecordingResponse)
def create_recording(
    body: RecordingCreateRequest,
    db: Session = Depends(get_db),
):
    recording_service = RecordingService(db)
    oss_service = get_oss_service()

    oss_file_path = oss_service.object_key_for_recording_with_ext(body.recording_id, body.file_ext)

    rec = recording_service.create_or_get_recording(
        device_id=body.device_id,
        recording_id=body.recording_id,
        start_at=body.start_at,
        end_at=body.end_at,
        timezone_str=body.timezone,
        oss_file_path=oss_file_path,
    )

    return RecordingResponse(
        device_id=rec.device_id,
        recording_id=rec.recording_id,
        start_at=rec.start_at,
        end_at=rec.end_at,
        timezone=rec.timezone,
        oss_file_path=rec.oss_file_path,
        status=rec.status,
    )


@router.get("/{recording_id}", response_model=RecordingResponse)
def get_recording(
    recording_id: str,
    db: Session = Depends(get_db),
):
    recording_service = RecordingService(db)
    rec = recording_service.get_recording(recording_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    return RecordingResponse(
        device_id=rec.device_id,
        recording_id=rec.recording_id,
        start_at=rec.start_at,
        end_at=rec.end_at,
        timezone=rec.timezone,
        oss_file_path=rec.oss_file_path,
        status=rec.status,
    )


class RecordingDeleteRequest(BaseModel):
    recording_id: str


@router.post("/{recording_id}/delete")
def delete_recording(
    recording_id: str,
    db: Session = Depends(get_db),
):
    recording_service = RecordingService(db)
    oss_service = get_oss_service()

    rec = recording_service.get_recording(recording_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    oss_service.delete_object(recording_id)
    recording_service.delete_recording(recording_id)

    return {"data": {"recording_id": recording_id, "deleted": True}}


