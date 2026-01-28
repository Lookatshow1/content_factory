from fastapi import APIRouter
from app.api.v1 import videos

router = APIRouter()
router.include_router(videos.router, prefix="/videos", tags=["Videos"])
