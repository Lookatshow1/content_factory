"""
Publishing models - track video publishing to various platforms.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Platform(str, enum.Enum):
    """Supported publishing platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    VK = "vk"
    TELEGRAM = "telegram"


class PublishingStatus(str, enum.Enum):
    """Publishing task status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class PublishingTask(Base):
    """
    Track publishing of a video to a specific platform.
    One video can have multiple publishing tasks (one per platform).
    """

    __tablename__ = "publishing_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    video_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("videos.id"), nullable=False
    )

    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    status: Mapped[PublishingStatus] = mapped_column(
        Enum(PublishingStatus), default=PublishingStatus.PENDING
    )

    # Platform-specific data
    platform_video_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Custom metadata per platform
    custom_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_hashtags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Analytics (updated periodically)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<PublishingTask(video_id={self.video_id}, platform={self.platform}, status={self.status})>"
