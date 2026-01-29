from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.db.models import TranscriptSegment


class TranscriptService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def replace_segments(
        self,
        recording_id: str,
        segments: List[Dict[str, Any]],
        asr_model: str | None = None,
    ) -> None:
        self.db.query(TranscriptSegment).filter(TranscriptSegment.recording_id == recording_id).delete()
        self.db.commit()

        for i, seg in enumerate(segments):
            item = TranscriptSegment(
                recording_id=recording_id,
                segment_index=int(seg.get("segment_index", i)),
                start_ms=int(seg.get("start_ms", 0)),
                end_ms=int(seg.get("end_ms", 0)),
                text=str(seg.get("text", "")),
                confidence=str(seg.get("confidence")) if seg.get("confidence") is not None else None,
                asr_model=asr_model,
            )
            self.db.add(item)

        self.db.commit()

    def list_segments(self, recording_id: str) -> List[TranscriptSegment]:
        return (
            self.db.query(TranscriptSegment)
            .filter(TranscriptSegment.recording_id == recording_id)
            .order_by(TranscriptSegment.segment_index.asc())
            .all()
        )


