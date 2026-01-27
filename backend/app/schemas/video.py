"""
Video schemas for API requests/responses.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.video import VideoStatus, VideoType


class VideoBase(BaseModel):
    """Base video schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    topic: Optional[str] = None
    niche: Optional[str] = None
    style: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)


class VideoCreate(VideoBase):
    """Schema for creating a video."""
    video_type: VideoType = VideoType.AVATAR
    duration_seconds: int = Field(default=45, ge=15, le=180)
    voice_id: Optional[str] = None
    avatar_id: Optional[str] = None
    script: Optional[str] = None  # If provided, skip script generation
    scheduled_at: Optional[datetime] = None


class VideoUpdate(BaseModel):
    """Schema for updating a video."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    script: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None


class VideoResponse(BaseModel):
    """Schema for video response."""
    id: int
    title: str
    description: Optional[str]
    script: Optional[str]
    hashtags: List[str]
    topic: Optional[str]
    niche: Optional[str]
    style: Optional[str]
    video_type: VideoType
    duration_seconds: int
    voice_id: Optional[str]
    avatar_id: Optional[str]
    status: VideoStatus
    error_message: Optional[str]
    audio_path: Optional[str]
    video_raw_path: Optional[str]
    video_final_path: Optional[str]
    thumbnail_path: Optional[str]
    scheduled_at: Optional[datetime]
    is_auto_generated: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """Schema for paginated video list."""
    items: List[VideoResponse]
    total: int
    page: int
    per_page: int
    pages: int


class GenerateVideoRequest(BaseModel):
    """
    Request to generate a video automatically.
    Just provide topic/niche and the system handles everything.
    """
    topic: str = Field(..., description="Topic for the video (e.g., 'AI news today')")
    niche: str = Field(default="technology", description="Content niche")
    style: str = Field(default="educational", description="Video style")
    video_type: VideoType = Field(default=VideoType.AVATAR)
    duration_seconds: int = Field(default=45, ge=15, le=180)
    voice_id: Optional[str] = None
    avatar_id: Optional[str] = None
    auto_publish: bool = Field(default=True, description="Auto-publish when ready")
    platforms: List[str] = Field(
        default=["youtube", "tiktok", "vk", "telegram", "instagram"]
    )
