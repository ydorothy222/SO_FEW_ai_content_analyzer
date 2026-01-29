import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config import get_settings
from src.db import get_db, Base, engine
from src.services.oss_service import get_oss_service
from src.services.recording_service import RecordingService


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/local-dev", tags=["local-dev"])


class LocalIngestRequest(BaseModel):
    local_path: str = Field(..., description="本机音频文件路径（仅 dev 环境）")
    device_id: str = Field("local-test-device")
    recording_id: str | None = Field(None, description="不传则自动生成 deviceId_timestamp")
    start_at: int | None = Field(None)
    end_at: int | None = Field(None)
    timezone: str = Field("Asia/Shanghai")


@router.get("/config-check")
def config_check():
    settings = get_settings()
    return {
        "data": {
            "env": settings.app.env,
            "dashscope_api_key_set": bool(settings.dashscope.api_key),
            "oss_endpoint": settings.oss.endpoint,
            "oss_bucket": settings.oss.bucket,
            "oss_access_key_id_set": bool(settings.oss.access_key_id),
            "oss_access_key_secret_set": bool(settings.oss.access_key_secret),
        }
    }


@router.post("/ingest-to-oss")
def ingest_to_oss(body: LocalIngestRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.app.env != "dev":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="local-dev endpoints are only enabled in dev")

    p = Path(body.local_path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=400, detail="local_path not found")

    ext = p.suffix.lstrip(".").lower() or "wav"
    recording_id = body.recording_id or f"{body.device_id}_{int(time.time())}"

    start_at = body.start_at or int(time.time())
    end_at = body.end_at or (start_at + 3600)

    oss = get_oss_service()
    object_key = oss.object_key_for_recording_with_ext(recording_id, ext)

    rec = RecordingService(db).create_or_get_recording(
        device_id=body.device_id,
        recording_id=recording_id,
        start_at=start_at,
        end_at=end_at,
        timezone_str=body.timezone,
        oss_file_path=object_key,
    )

    # 上传到 OSS
    oss.upload_local_file(object_key, str(p))

    return {"data": {"recording_id": rec.recording_id, "object_key": object_key, "uploaded": True}}


