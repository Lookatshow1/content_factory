"""
System API endpoints - configuration, status, etc.
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.video import Video, VideoStatus
from app.models.publishing import PublishingTask, PublishingStatus
from app.models.content_plan import ContentPlan

router = APIRouter()


@router.get("/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get system status and configuration check."""
    # Check API keys configuration
    api_keys_status = {
        "anthropic": bool(settings.anthropic_api_key),
        "elevenlabs": bool(settings.elevenlabs_api_key),
        "heygen": bool(settings.heygen_api_key),
        "fal": bool(settings.fal_api_key),
        "openai": bool(settings.openai_api_key),
    }

    publishing_status = {
        "youtube": bool(settings.youtube_client_id and settings.youtube_client_secret),
        "tiktok": bool(settings.tiktok_client_key),
        "vk": bool(settings.vk_access_token),
        "telegram": bool(settings.telegram_bot_token),
        "instagram": bool(settings.instagram_access_token),
    }

    # Get video stats
    video_stats = {}
    for status in VideoStatus:
        result = await db.execute(
            select(func.count()).select_from(Video).where(Video.status == status)
        )
        video_stats[status.value] = result.scalar() or 0

    # Get publishing stats
    publishing_stats = {}
    for status in PublishingStatus:
        result = await db.execute(
            select(func.count())
            .select_from(PublishingTask)
            .where(PublishingTask.status == status)
        )
        publishing_stats[status.value] = result.scalar() or 0

    # Active content plans
    active_plans_result = await db.execute(
        select(func.count())
        .select_from(ContentPlan)
        .where(ContentPlan.is_active == True)
    )
    active_plans = active_plans_result.scalar() or 0

    return {
        "status": "healthy",
        "version": "1.0.0",
        "configuration": {
            "ai_services": api_keys_status,
            "publishing_platforms": publishing_status,
            "videos_per_week": settings.videos_per_week,
        },
        "statistics": {
            "videos": video_stats,
            "publishing": publishing_stats,
            "active_content_plans": active_plans,
        },
        "ready": all(api_keys_status.values()) and any(publishing_status.values()),
    }


@router.get("/config")
async def get_configuration() -> Dict[str, Any]:
    """Get current configuration (non-sensitive)."""
    return {
        "videos_per_week": settings.videos_per_week,
        "default_video_duration": settings.default_video_duration,
        "default_voice_id": settings.default_voice_id,
        "supported_platforms": ["youtube", "tiktok", "vk", "telegram", "instagram"],
        "supported_video_types": ["avatar", "ai_generated", "stock_footage"],
    }


@router.get("/voices")
async def get_available_voices() -> Dict[str, Any]:
    """Get available ElevenLabs voices."""
    # This would ideally fetch from ElevenLabs API
    # For now, return common presets
    return {
        "voices": [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
            {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
            {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female"},
            {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male"},
            {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male"},
            {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male"},
        ]
    }


@router.get("/avatars")
async def get_available_avatars() -> Dict[str, Any]:
    """Get available HeyGen avatars."""
    # This would ideally fetch from HeyGen API
    return {
        "avatars": [
            {"id": "Angela-inblackskirt-20220820", "name": "Angela", "style": "professional"},
            {"id": "Anna_public_3_20240108", "name": "Anna", "style": "casual"},
            {"id": "josh_lite3_20230714", "name": "Josh", "style": "business"},
            {"id": "Kayla-incasualsuit-20220818", "name": "Kayla", "style": "modern"},
            {"id": "lisa_3qzj_20230421", "name": "Lisa", "style": "friendly"},
        ],
        "note": "For full avatar list, connect HeyGen API key and use /api/v1/system/sync-avatars"
    }
