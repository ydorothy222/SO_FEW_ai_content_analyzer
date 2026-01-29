from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import (
    recordings,
    oss,
    transcribe,
    analysis,
    qa,
    pipeline,
    local_dev,
    content_workflow,
    auth,
    admin,
)
from .db import Base, engine

app = FastAPI(title="Sofew Intelligent Companion API", version="0.1.0")

_static_dir = Path(__file__).resolve().parent / "static"


@app.on_event("startup")
def ensure_tables():
    """确保用户与用量表存在。"""
    import src.db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def root():
    """根路径重定向到内容永动机页面。"""
    return RedirectResponse("/content-workflow", status_code=302)


@app.get("/content-workflow", include_in_schema=False)
def content_workflow_page():
    """内容永动机前端页面。"""
    index = _static_dir / "index.html"
    if index.is_file():
        return FileResponse(index)
    return RedirectResponse("/docs")


if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(recordings.router, prefix="/v1")
app.include_router(oss.router, prefix="/v1")
app.include_router(transcribe.router, prefix="/v1")
app.include_router(analysis.router, prefix="/v1")
app.include_router(qa.router, prefix="/v1")
app.include_router(pipeline.router, prefix="/v1")
app.include_router(local_dev.router, prefix="/v1")
app.include_router(content_workflow.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")


