"""
Video model - represents a generated video and its pipeline stages.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, DateTime, Enum, JSON, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VideoStatus(str, enum.Enum):
    """Video production pipeline status."""
    PENDING = "pending"              # Waiting in queue
    GENERATING_SCRIPT = "generating_script"
    SCRIPT_READY = "script_ready"
    GENERATING_IMAGES = "generating_images"  # New: generating scene images
    IMAGES_READY = "images_ready"
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
    AVATAR = "avatar"                    # HeyGen talking head only
    AVATAR_WITH_INSERTS = "avatar_inserts"  # Avatar + AI images/video inserts
    AI_GENERATED = "ai_generated"        # Kling/Runway AI video
    STOCK_FOOTAGE = "stock_footage"      # Stock video + voiceover
    IMAGES_SLIDESHOW = "images_slideshow"  # AI images as slideshow


class OutputMode(str, enum.Enum):
    """Output rendering mode."""
    AVATAR_ONLY = "avatar_only"          # Just the avatar talking
    AVATAR_WITH_INSERTS = "avatar_inserts"  # Avatar + B-roll inserts
    INSERTS_ONLY = "inserts_only"        # Only AI-generated visuals
    SPLIT_SCREEN = "split_screen"        # Avatar on side, visuals in main


class Video(Base):
    """Video entity representing a single piece of content."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Custom content options (NEW)
    use_custom_script: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_script_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Base prompt for all images

    # Topic/Niche for generation
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    niche: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Video settings
    video_type: Mapped[VideoType] = mapped_column(
        Enum(VideoType), default=VideoType.AVATAR
    )
    output_mode: Mapped[OutputMode] = mapped_column(
        Enum(OutputMode), default=OutputMode.AVATAR_ONLY
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=45)
    voice_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Image/Insert settings (NEW)
    insert_percentage: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1, how much of video is inserts
    images_per_scene: Mapped[int] = mapped_column(Integer, default=1)
    use_stock_footage: Mapped[bool] = mapped_column(Boolean, default=False)
    stock_search_query: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Pipeline status
    status: Mapped[VideoStatus] = mapped_column(
        Enum(VideoStatus), default=VideoStatus.PENDING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generated files
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_raw_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_final_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_avatar_only_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Avatar-only version
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

    # Relationships
    scenes: Mapped[list["VideoScene"]] = relationship(
        "VideoScene", back_populates="video", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Video(id={self.id}, title='{self.title}', status={self.status})>"


class SceneType(str, enum.Enum):
    """Type of scene content."""
    AI_IMAGE = "ai_image"        # AI-generated image
    AI_VIDEO = "ai_video"        # AI-generated video clip
    STOCK_VIDEO = "stock_video"  # Stock footage
    STOCK_IMAGE = "stock_image"  # Stock image
    AVATAR = "avatar"            # Avatar segment


class VideoScene(Base):
    """Individual scene/segment within a video with its own visual content."""

    __tablename__ = "video_scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(Integer, ForeignKey("videos.id"), nullable=False)

    # Scene positioning
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Order in video
    start_time: Mapped[float] = mapped_column(Float, nullable=True)  # Start time in seconds
    end_time: Mapped[float] = mapped_column(Float, nullable=True)    # End time in seconds
    duration: Mapped[float] = mapped_column(Float, nullable=True)    # Duration in seconds

    # Content
    scene_type: Mapped[SceneType] = mapped_column(Enum(SceneType), default=SceneType.AI_IMAGE)
    script_segment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Part of script for this scene

    # Image/Video generation
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Specific prompt for this scene
    generated_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # AI-enhanced prompt

    # Generated content
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_clip_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Stock footage info
    stock_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pexels, pixabay, etc
    stock_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stock_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    is_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)  # User can reject and regenerate
    generation_attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    video: Mapped["Video"] = relationship("Video", back_populates="scenes")

    def __repr__(self) -> str:
        return f"<VideoScene(id={self.id}, video_id={self.video_id}, order={self.order_index})>"
