from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.video import Video
from pydantic import BaseModel

router = APIRouter()

class VideoCreate(BaseModel):
    topic: str
    title: str

@router.post("/")
async def create_video(payload: VideoCreate, db: AsyncSession = Depends(get_db)):
    video = Video(title=payload.title, topic=payload.topic)
    db.add(video)
    await db.commit()
    await db.refresh(video)
    # Trigger celery task here
    return video
