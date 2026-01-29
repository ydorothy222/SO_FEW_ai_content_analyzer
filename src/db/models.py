from sqlalchemy import Column, Integer, String, BigInteger, TIMESTAMP, Text, ForeignKey
from sqlalchemy.sql import func

from .session import Base


# --- ToC 用户与用量 ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False, default="user")  # admin | user
    balance = Column(Integer, nullable=False, default=0)  # 剩余可用次数
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class GuestUsage(Base):
    __tablename__ = "guest_usage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    guest_id = Column(String(64), unique=True, index=True, nullable=False)
    count = Column(Integer, nullable=False, default=0)  # 已使用次数
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())


class RecordingMeta(Base):
    __tablename__ = "recording_meta"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(64), index=True, nullable=False)
    recording_id = Column(String(128), unique=True, nullable=False, index=True)
    start_at = Column(BigInteger, nullable=False)
    end_at = Column(BigInteger, nullable=False)
    timezone = Column(String(32), nullable=False, default="Asia/Shanghai")
    oss_file_path = Column(String(256), nullable=False)
    status = Column(String(32), nullable=False, default="uploaded")
    error_code = Column(String(64), nullable=True)
    error_message = Column(String(256), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    create_time = Column(TIMESTAMP, nullable=False, server_default=func.now())


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recording_id = Column(String(128), ForeignKey("recording_meta.recording_id"), index=True, nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_ms = Column(Integer, nullable=False, default=0)
    end_ms = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    confidence = Column(String(32), nullable=True)
    asr_model = Column(String(64), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


class RecordingAnalysis(Base):
    __tablename__ = "recording_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recording_id = Column(String(128), ForeignKey("recording_meta.recording_id"), index=True, nullable=False)
    analysis_version = Column(String(32), nullable=False, default="v1")
    summary = Column(Text, nullable=True)
    people_json = Column(Text, nullable=True)
    issues_json = Column(Text, nullable=True)
    suggestions_json = Column(Text, nullable=True)
    sources_json = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


