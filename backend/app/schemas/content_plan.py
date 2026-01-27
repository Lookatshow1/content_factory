"""
Content Plan schemas for API.
"""
from datetime import datetime, time
from typing import Optional, List

from pydantic import BaseModel, Field


class ContentPlanBase(BaseModel):
    """Base content plan schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    niche: str = Field(..., min_length=1, max_length=100)
    topics: List[str] = Field(default_factory=list)
    style: str = Field(default="educational")
    tone: str = Field(default="professional")


class ContentPlanCreate(ContentPlanBase):
    """Schema for creating a content plan."""
    video_type: str = Field(default="avatar")
    voice_id: Optional[str] = None
    avatar_id: Optional[str] = None
    duration_seconds: int = Field(default=45, ge=15, le=180)
    videos_per_week: int = Field(default=5, ge=1, le=21)
    publish_days: List[int] = Field(
        default=[0, 1, 2, 3, 4],
        description="Days of week (0=Mon, 6=Sun)"
    )
    publish_time: str = Field(default="12:00", description="HH:MM format")
    platforms: List[str] = Field(
        default=["youtube", "tiktok", "vk", "telegram", "instagram"]
    )


class ContentPlanUpdate(BaseModel):
    """Schema for updating a content plan."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    niche: Optional[str] = None
    topics: Optional[List[str]] = None
    style: Optional[str] = None
    tone: Optional[str] = None
    video_type: Optional[str] = None
    voice_id: Optional[str] = None
    avatar_id: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=15, le=180)
    videos_per_week: Optional[int] = Field(None, ge=1, le=21)
    publish_days: Optional[List[int]] = None
    publish_time: Optional[str] = None
    platforms: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ContentPlanItemResponse(BaseModel):
    """Schema for content plan item response."""
    id: int
    plan_id: int
    video_id: Optional[int]
    topic: str
    scheduled_date: datetime
    is_generated: bool
    is_published: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ContentPlanResponse(BaseModel):
    """Schema for content plan response."""
    id: int
    name: str
    description: Optional[str]
    niche: str
    topics: List[str]
    style: str
    tone: str
    video_type: str
    voice_id: Optional[str]
    avatar_id: Optional[str]
    duration_seconds: int
    videos_per_week: int
    publish_days: List[int]
    publish_time: str
    platforms: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    items: List[ContentPlanItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
