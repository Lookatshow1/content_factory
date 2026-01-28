import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, DateTime, Enum, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    ADDING_SUBTITLES = "adding_subtitles"
    COMPLETED = "completed"
    FAILED = "failed"

class Platform(str, enum.Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    VK = "vk"
    TELEGRAM = "telegram"

class Video(Base):
    __tablename__ = "videos"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    topic: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[VideoStatus] = mapped_column(Enum(VideoStatus), default=VideoStatus.PENDING)
    script: Mapped[Optional[str]] = mapped_column(Text)
    voice_url: Mapped[Optional[str]] = mapped_column(String(500))
    video_url: Mapped[Optional[str]] = mapped_column(String(500))
    final_video_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    publishing_tasks: Mapped[List["PublishingTask"]] = relationship(back_populates="video", cascade="all, delete-orphan")

class PublishingTask(Base):
    __tablename__ = "publishing_tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_message: Optional[Mapped[str]] = mapped_column(Text)
    
    video: Mapped["Video"] = relationship(back_populates="publishing_tasks")
