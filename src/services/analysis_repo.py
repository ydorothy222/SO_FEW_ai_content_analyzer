import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from src.db.models import RecordingAnalysis


class AnalysisRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_analysis(self, recording_id: str, analysis: Dict[str, Any], version: str = "v1") -> RecordingAnalysis:
        existing = (
            self.db.query(RecordingAnalysis)
            .filter(RecordingAnalysis.recording_id == recording_id, RecordingAnalysis.analysis_version == version)
            .one_or_none()
        )
        if existing is None:
            existing = RecordingAnalysis(recording_id=recording_id, analysis_version=version)
            self.db.add(existing)

        existing.summary = analysis.get("summary")
        existing.people_json = json.dumps(analysis.get("people", []), ensure_ascii=False)
        existing.issues_json = json.dumps(analysis.get("issues", []), ensure_ascii=False)
        existing.suggestions_json = json.dumps(analysis.get("suggestions", []), ensure_ascii=False)
        existing.sources_json = json.dumps(analysis.get("sources", []), ensure_ascii=False)

        self.db.commit()
        self.db.refresh(existing)
        return existing

    def get_analysis(self, recording_id: str, version: str = "v1") -> Optional[RecordingAnalysis]:
        return (
            self.db.query(RecordingAnalysis)
            .filter(RecordingAnalysis.recording_id == recording_id, RecordingAnalysis.analysis_version == version)
            .one_or_none()
        )


