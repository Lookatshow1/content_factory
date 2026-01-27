"""
Video model - represents a generated video and its pipeline stages.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, Enum, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VideoStatus(str, enum.Enum):
    """Video production pipeline status."""
    PENDING = "pending"              # Waiting in queue
    GENERATING_SCRIPT = "generating_script"
    SCRIPT_READY = "script_ready"
    GENERATING_AUDIO = "generating_audio"
    AUDIO_READY = "audio_ready"
    GENERATING_VIDEO = "generating_video"
    VIDEO_READY = "video_ready"
    ADDING_SUBTITLES = "adding_subtitles"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoType(str, enum.Enum):
    """Type of video generation."""
    AVATAR = "avatar"          # HeyGen talking head
    AI_GENERATED = "ai_generated"  # Kling/Runway AI video
    STOCK_FOOTAGE = "stock_footage"  # Stock video + voiceover


class Video(Base):
    """Video entity representing a single piece of content."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Topic/Niche for generation
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    niche: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Video settings
    video_type: Mapped[VideoType] = mapped_column(
        Enum(VideoType), default=VideoType.AVATAR
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=45)
    voice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Pipeline status
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus), default=VideoStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generated files
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_raw_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_final_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    subtitles_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # External IDs from AI services
    heygen_video_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    elevenlabs_audio_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title='{self.title}', status={self.status})>"
