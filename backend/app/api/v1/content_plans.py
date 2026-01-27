"""
Content Plans API endpoints.
"""
from datetime import datetime, time
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.content_plan import ContentPlan, ContentPlanItem
from app.schemas.content_plan import (
    ContentPlanCreate,
    ContentPlanUpdate,
    ContentPlanResponse,
)
from app.workers.tasks import schedule_content_plan

router = APIRouter()


@router.get("", response_model=List[ContentPlanResponse])
async def list_content_plans(
    db: AsyncSession = Depends(get_db),
):
    """List all content plans."""
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .order_by(ContentPlan.created_at.desc())
    )
    plans = result.scalars().all()

    return [
        ContentPlanResponse(
            **{
                **plan.__dict__,
                "publish_time": plan.publish_time.strftime("%H:%M"),
                "items": plan.items,
            }
        )
        for plan in plans
    ]


@router.post("", response_model=ContentPlanResponse, status_code=201)
async def create_content_plan(
    plan_in: ContentPlanCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new content plan."""
    # Parse publish time
    hours, minutes = map(int, plan_in.publish_time.split(":"))
    publish_time = time(hours, minutes)

    plan = ContentPlan(
        name=plan_in.name,
        description=plan_in.description,
        niche=plan_in.niche,
        topics=plan_in.topics,
        style=plan_in.style,
        tone=plan_in.tone,
        video_type=plan_in.video_type,
        voice_id=plan_in.voice_id,
        avatar_id=plan_in.avatar_id,
        duration_seconds=plan_in.duration_seconds,
        videos_per_week=plan_in.videos_per_week,
        publish_days=plan_in.publish_days,
        publish_time=publish_time,
        platforms=plan_in.platforms,
        is_active=True,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)

    # Schedule initial content
    schedule_content_plan.delay(plan.id)

    return ContentPlanResponse(
        **{
            **plan.__dict__,
            "publish_time": plan.publish_time.strftime("%H:%M"),
            "items": [],
        }
    )


@router.get("/{plan_id}", response_model=ContentPlanResponse)
async def get_content_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific content plan."""
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .where(ContentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Content plan not found")

    return ContentPlanResponse(
        **{
            **plan.__dict__,
            "publish_time": plan.publish_time.strftime("%H:%M"),
            "items": plan.items,
        }
    )


@router.patch("/{plan_id}", response_model=ContentPlanResponse)
async def update_content_plan(
    plan_id: int,
    plan_in: ContentPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a content plan."""
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .where(ContentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Content plan not found")

    update_data = plan_in.model_dump(exclude_unset=True)

    # Handle publish_time conversion
    if "publish_time" in update_data:
        hours, minutes = map(int, update_data["publish_time"].split(":"))
        update_data["publish_time"] = time(hours, minutes)

    for field, value in update_data.items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)

    return ContentPlanResponse(
        **{
            **plan.__dict__,
            "publish_time": plan.publish_time.strftime("%H:%M"),
            "items": plan.items,
        }
    )


@router.delete("/{plan_id}", status_code=204)
async def delete_content_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a content plan."""
    result = await db.execute(select(ContentPlan).where(ContentPlan.id == plan_id))
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Content plan not found")

    await db.delete(plan)
    await db.commit()


@router.post("/{plan_id}/activate", response_model=ContentPlanResponse)
async def activate_content_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Activate a content plan."""
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .where(ContentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Content plan not found")

    plan.is_active = True
    await db.commit()
    await db.refresh(plan)

    # Re-schedule content
    schedule_content_plan.delay(plan.id)

    return ContentPlanResponse(
        **{
            **plan.__dict__,
            "publish_time": plan.publish_time.strftime("%H:%M"),
            "items": plan.items,
        }
    )


@router.post("/{plan_id}/deactivate", response_model=ContentPlanResponse)
async def deactivate_content_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a content plan."""
    result = await db.execute(
        select(ContentPlan)
        .options(selectinload(ContentPlan.items))
        .where(ContentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail="Content plan not found")

    plan.is_active = False
    await db.commit()
    await db.refresh(plan)

    return ContentPlanResponse(
        **{
            **plan.__dict__,
            "publish_time": plan.publish_time.strftime("%H:%M"),
            "items": plan.items,
        }
    )
