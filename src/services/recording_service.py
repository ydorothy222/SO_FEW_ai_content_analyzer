from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import RecordingMeta


class RecordingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_or_get_recording(
        self,
        device_id: str,
        recording_id: str,
        start_at: int,
        end_at: int,
        timezone_str: str,
        oss_file_path: str,
    ) -> RecordingMeta:
        existing = (
            self.db.query(RecordingMeta)
            .filter(RecordingMeta.recording_id == recording_id)
            .one_or_none()
        )
        if existing:
            # 若首次创建时没写对 oss_file_path，这里允许补齐（但不覆盖已有有效值）
            if not existing.oss_file_path and oss_file_path:
                existing.oss_file_path = oss_file_path
                self.db.commit()
            return existing

        now_utc = datetime.now(timezone.utc)
        rec = RecordingMeta(
            device_id=device_id,
            recording_id=recording_id,
            start_at=start_at,
            end_at=end_at,
            timezone=timezone_str,
            oss_file_path=oss_file_path,
            status="uploaded",
            retry_count=0,
            create_time=now_utc,
        )
        self.db.add(rec)
        self.db.commit()
        self.db.refresh(rec)
        return rec

    def get_recording(self, recording_id: str) -> Optional[RecordingMeta]:
        return (
            self.db.query(RecordingMeta)
            .filter(RecordingMeta.recording_id == recording_id)
            .one_or_none()
        )

    def delete_recording(self, recording_id: str) -> None:
        rec = (
            self.db.query(RecordingMeta)
            .filter(RecordingMeta.recording_id == recording_id)
            .one_or_none()
        )
        if rec is None:
            return
        self.db.delete(rec)
        self.db.commit()


