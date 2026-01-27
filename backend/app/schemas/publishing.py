"""
Publishing schemas for API.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.publishing import Platform, PublishingStatus


class PublishingTaskCreate(BaseModel):
    """Schema for creating a publishing task."""
    video_id: int
    platform: Platform
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None
    custom_hashtags: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class PublishingTaskResponse(BaseModel):
    """Schema for publishing task response."""
    id: int
    video_id: int
    platform: Platform
    status: PublishingStatus
    platform_video_id: Optional[str]
    platform_url: Optional[str]
    custom_title: Optional[str]
    custom_description: Optional[str]
    custom_hashtags: Optional[List[str]]
    error_message: Optional[str]
    retry_count: int
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    views: int
    likes: int
    comments: int
    shares: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublishRequest(BaseModel):
    """Request to publish a video to multiple platforms."""
    video_id: int
    platforms: List[Platform] = Field(
        default=[
            Platform.YOUTUBE,
            Platform.TIKTOK,
            Platform.VK,
            Platform.TELEGRAM,
            Platform.INSTAGRAM,
        ]
    )
    scheduled_at: Optional[datetime] = None


class PublishingStatsResponse(BaseModel):
    """Aggregated publishing stats."""
    total_published: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    by_platform: dict
