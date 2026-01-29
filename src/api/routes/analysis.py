import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db import get_db, Base, engine
from src.services.analysis_repo import AnalysisRepo
from src.services.analysis_service import AnalysisService
from src.services.recording_service import RecordingService
from src.services.transcript_service import TranscriptService


Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/{recording_id}/run")
def run_analysis(recording_id: str, db: Session = Depends(get_db)):
    recording_service = RecordingService(db)
    rec = recording_service.get_recording(recording_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    transcript_service = TranscriptService(db)
    segs = transcript_service.list_segments(recording_id)
    if not segs:
        raise HTTPException(status_code=400, detail="No transcript segments found; run transcribe first.")

    payload = [
        {"segment_index": s.segment_index, "start_ms": s.start_ms, "end_ms": s.end_ms, "text": s.text}
        for s in segs
    ]
    analysis = AnalysisService().analyze_transcript(payload)
    repo = AnalysisRepo(db)
    saved = repo.upsert_analysis(recording_id, analysis, version="v1")

    rec.status = "ready"
    db.commit()

    return {"data": {"recording_id": recording_id, "analysis_version": saved.analysis_version, "status": rec.status}}


@router.get("/{recording_id}")
def get_analysis(recording_id: str, db: Session = Depends(get_db)):
    repo = AnalysisRepo(db)
    item = repo.get_analysis(recording_id, version="v1")
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return {
        "data": {
            "recording_id": recording_id,
            "analysis_version": item.analysis_version,
            "summary": item.summary,
            "people": json.loads(item.people_json or "[]"),
            "issues": json.loads(item.issues_json or "[]"),
            "suggestions": json.loads(item.suggestions_json or "[]"),
            "sources": json.loads(item.sources_json or "[]"),
        }
    }


