"""
Videos API endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.video import Video, VideoStatus
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoListResponse,
    GenerateVideoRequest,
)
from app.workers.tasks import generate_video_pipeline

router = APIRouter()


@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[VideoStatus] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all videos with pagination."""
    query = select(Video).order_by(Video.created_at.desc())

    if status:
        query = query.where(Video.status == status)

    # Get total count
    count_query = select(func.count()).select_from(Video)
    if status:
        count_query = count_query.where(Video.status == status)
    total = await db.scalar(count_query)

    # Get paginated results
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    videos = result.scalars().all()

    return VideoListResponse(
        items=[VideoResponse.model_validate(v) for v in videos],
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=(total or 0 + per_page - 1) // per_page,
    )


@router.post("", response_model=VideoResponse, status_code=201)
async def create_video(
    video_in: VideoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new video (manual creation)."""
    video = Video(
        title=video_in.title,
        description=video_in.description,
        script=video_in.script,
        topic=video_in.topic,
        niche=video_in.niche,
        style=video_in.style,
        hashtags=video_in.hashtags,
        video_type=video_in.video_type,
        duration_seconds=video_in.duration_seconds,
        voice_id=video_in.voice_id,
        avatar_id=video_in.avatar_id,
        scheduled_at=video_in.scheduled_at,
        status=VideoStatus.PENDING,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return VideoResponse.model_validate(video)


@router.post("/generate", response_model=VideoResponse, status_code=202)
async def generate_video(
    request: GenerateVideoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a video automatically from a topic.
    This triggers the full pipeline: script -> audio -> video -> subtitles -> publish.
    """
    # Create video record
    video = Video(
        title=f"Video about {request.topic}",  # Will be updated by AI
        topic=request.topic,
        niche=request.niche,
        style=request.style,
        video_type=request.video_type,
        duration_seconds=request.duration_seconds,
        voice_id=request.voice_id,
        avatar_id=request.avatar_id,
        status=VideoStatus.PENDING,
        is_auto_generated=True,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Trigger async pipeline
    generate_video_pipeline.delay(
        video_id=video.id,
        auto_publish=request.auto_publish,
        platforms=request.platforms,
    )

    return VideoResponse.model_validate(video)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific video by ID."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return VideoResponse.model_validate(video)


@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video(
    video_id: int,
    video_in: VideoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a video."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    update_data = video_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)

    await db.commit()
    await db.refresh(video)
    return VideoResponse.model_validate(video)


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a video."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    await db.delete(video)
    await db.commit()


@router.post("/{video_id}/regenerate", response_model=VideoResponse, status_code=202)
async def regenerate_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a failed video."""
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Reset status
    video.status = VideoStatus.PENDING
    video.error_message = None
    await db.commit()
    await db.refresh(video)

    # Trigger pipeline
    generate_video_pipeline.delay(video_id=video.id, auto_publish=True)

    return VideoResponse.model_validate(video)
