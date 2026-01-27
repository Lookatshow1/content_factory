"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import videos, content_plans, publishing, system

router = APIRouter()

router.include_router(videos.router, prefix="/videos", tags=["Videos"])
router.include_router(content_plans.router, prefix="/content-plans", tags=["Content Plans"])
router.include_router(publishing.router, prefix="/publishing", tags=["Publishing"])
router.include_router(system.router, prefix="/system", tags=["System"])
