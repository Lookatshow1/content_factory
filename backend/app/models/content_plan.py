"""
Content Plan models - for scheduling automated content generation.
"""
import enum
from datetime import datetime, time
from typing import Optional, List

from sqlalchemy import String, Text, Integer, DateTime, Enum, JSON, Boolean, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContentPlan(Base):
    """
    Content Plan - defines automatic content generation schedule.
    E.g., "Generate 5 videos per week about AI news"
    """

    __tablename__ = "content_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Content settings
    niche: Mapped[str] = mapped_column(String(100), nullable=False)
    topics: Mapped[list] = mapped_column(JSON, default=list)  # List of topics to rotate
    style: Mapped[str] = mapped_column(String(100), default="educational")
    tone: Mapped[str] = mapped_column(String(100), default="professional")

    # Generation settings
    video_type: Mapped[str] = mapped_column(String(50), default="avatar")
    voice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=45)

    # Schedule settings
    videos_per_week: Mapped[int] = mapped_column(Integer, default=5)
    publish_days: Mapped[list] = mapped_column(
        JSON, default=lambda: [0, 1, 2, 3, 4]  # Mon-Fri
    )
    publish_time: Mapped[time] = mapped_column(Time, default=time(12, 0))  # Noon

    # Target platforms
    platforms: Mapped[list] = mapped_column(
        JSON, default=lambda: ["youtube", "tiktok", "vk", "telegram", "instagram"]
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship
    items: Mapped[List["ContentPlanItem"]] = relationship(
        "ContentPlanItem", back_populates="plan", cascade="all, delete-orphan"
    )


class ContentPlanItem(Base):
    """
    Individual scheduled item within a content plan.
    Created automatically by the scheduler.
    """

    __tablename__ = "content_plan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content_plans.id"), nullable=False
    )
    video_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("videos.id"), nullable=True
    )

    # Scheduled content
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Status
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    plan: Mapped["ContentPlan"] = relationship("ContentPlan", back_populates="items")
