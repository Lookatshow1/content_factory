"""
Publishing API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.publishing import PublishingTask, Platform, PublishingStatus
from app.models.video import Video, VideoStatus
from app.schemas.publishing import (
    PublishingTaskCreate,
    PublishingTaskResponse,
    PublishRequest,
    PublishingStatsResponse,
)
from app.workers.tasks import publish_video_task

router = APIRouter()


@router.get("/tasks", response_model=List[PublishingTaskResponse])
async def list_publishing_tasks(
    video_id: Optional[int] = None,
    platform: Optional[Platform] = None,
    status: Optional[PublishingStatus] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List publishing tasks with filters."""
    query = select(PublishingTask).order_by(PublishingTask.created_at.desc())

    if video_id:
        query = query.where(PublishingTask.video_id == video_id)
    if platform:
        query = query.where(PublishingTask.platform == platform)
    if status:
        query = query.where(PublishingTask.status == status)

    query = query.limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return [PublishingTaskResponse.model_validate(t) for t in tasks]


@router.post("/publish", response_model=List[PublishingTaskResponse], status_code=202)
async def publish_video(
    request: PublishRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Publish a video to specified platforms.
    Creates publishing tasks and triggers async publishing.
    """
    # Check video exists and is completed
    result = await db.execute(select(Video).where(Video.id == request.video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready for publishing (status: {video.status})",
        )

    if not video.video_final_path:
        raise HTTPException(status_code=400, detail="Video file not found")

    tasks = []
    for platform in request.platforms:
        # Check if task already exists
        existing = await db.execute(
            select(PublishingTask).where(
                PublishingTask.video_id == request.video_id,
                PublishingTask.platform == platform,
            )
        )
        if existing.scalar_one_or_none():
            continue

        task = PublishingTask(
            video_id=request.video_id,
            platform=platform,
            status=PublishingStatus.PENDING,
            scheduled_at=request.scheduled_at,
        )
        db.add(task)
        tasks.append(task)

    await db.commit()

    # Trigger async publishing for each task
    for task in tasks:
        await db.refresh(task)
        publish_video_task.delay(task.id)

    return [PublishingTaskResponse.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=PublishingTaskResponse)
async def get_publishing_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific publishing task."""
    result = await db.execute(
        select(PublishingTask).where(PublishingTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Publishing task not found")

    return PublishingTaskResponse.model_validate(task)


@router.post("/tasks/{task_id}/retry", response_model=PublishingTaskResponse)
async def retry_publishing_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed publishing task."""
    result = await db.execute(
        select(PublishingTask).where(PublishingTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Publishing task not found")

    if task.status != PublishingStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Can only retry failed tasks",
        )

    task.status = PublishingStatus.PENDING
    task.error_message = None
    await db.commit()
    await db.refresh(task)

    publish_video_task.delay(task.id)

    return PublishingTaskResponse.model_validate(task)


@router.get("/stats", response_model=PublishingStatsResponse)
async def get_publishing_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated publishing statistics."""
    # Total published
    total_result = await db.execute(
        select(func.count()).where(
            PublishingTask.status == PublishingStatus.PUBLISHED
        )
    )
    total_published = total_result.scalar() or 0

    # Aggregated metrics
    metrics_result = await db.execute(
        select(
            func.sum(PublishingTask.views),
            func.sum(PublishingTask.likes),
            func.sum(PublishingTask.comments),
            func.sum(PublishingTask.shares),
        ).where(PublishingTask.status == PublishingStatus.PUBLISHED)
    )
    metrics = metrics_result.one()

    # Per-platform stats
    platform_stats = {}
    for platform in Platform:
        platform_result = await db.execute(
            select(
                func.count(),
                func.sum(PublishingTask.views),
                func.sum(PublishingTask.likes),
            )
            .where(PublishingTask.platform == platform)
            .where(PublishingTask.status == PublishingStatus.PUBLISHED)
        )
        p_stats = platform_result.one()
        platform_stats[platform.value] = {
            "count": p_stats[0] or 0,
            "views": p_stats[1] or 0,
            "likes": p_stats[2] or 0,
        }

    return PublishingStatsResponse(
        total_published=total_published,
        total_views=metrics[0] or 0,
        total_likes=metrics[1] or 0,
        total_comments=metrics[2] or 0,
        total_shares=metrics[3] or 0,
        by_platform=platform_stats,
    )
