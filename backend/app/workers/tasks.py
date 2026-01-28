"""
Celery tasks for video generation and publishing pipeline.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.celery_app import celery_app
from app.core.database import async_session_maker
from app.core.config import settings
from app.models.video import Video, VideoStatus, VideoType
from app.models.content_plan import ContentPlan, ContentPlanItem
from app.models.publishing import PublishingTask, Platform, PublishingStatus


def run_async(coro):
    """Helper to run async code in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def generate_video_pipeline(
    self,
    video_id: int,
    auto_publish: bool = True,
    platforms: Optional[List[str]] = None,
):
    """
    Complete video generation pipeline.
    1. Generate script (Claude)
    2. Generate audio (ElevenLabs)
    3. Generate video (HeyGen/Kling)
    4. Add subtitles
    5. Final render
    6. Optionally publish
    """
    return run_async(_generate_video_pipeline(
        video_id, auto_publish, platforms or []
    ))


async def _generate_video_pipeline(
    video_id: int,
    auto_publish: bool,
    platforms: List[str],
):
    """Async implementation of video pipeline."""
    from app.services.ai.script_generator import ScriptGenerator
    from app.services.ai.voice_generator import VoiceGenerator
    from app.services.ai.video_generator import VideoGenerator
    from app.services.video.subtitles import SubtitleGenerator
    from app.services.video.processor import VideoProcessor

    async with async_session_maker() as db:
        # Get video
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise ValueError(f"Video {video_id} not found")

        try:
            # Step 1: Generate Script
            if not video.script:
                video.status = VideoStatus.GENERATING_SCRIPT
                await db.commit()

                script_gen = ScriptGenerator()
                script_result = await script_gen.generate(
                    topic=video.topic or "interesting topic",
                    niche=video.niche or "technology",
                    style=video.style or "educational",
                    duration_seconds=video.duration_seconds,
                )

                video.title = script_result.title
                video.description = script_result.description
                video.script = script_result.script
                video.hashtags = script_result.hashtags
                video.status = VideoStatus.SCRIPT_READY
                await db.commit()

            # Step 2: Generate Audio
            video.status = VideoStatus.GENERATING_AUDIO
            await db.commit()

            voice_gen = VoiceGenerator()
            audio_path = await voice_gen.generate(
                text=video.script,
                voice_id=video.voice_id or settings.default_voice_id,
            )

            video.audio_path = audio_path
            video.status = VideoStatus.AUDIO_READY
            await db.commit()

            # Step 3: Generate Video
            video.status = VideoStatus.GENERATING_VIDEO
            await db.commit()

            video_gen = VideoGenerator()

            if video.video_type == VideoType.AVATAR:
                # Use HeyGen for avatar video
                video_path = await video_gen.generate_avatar_video(
                    script=video.script,
                    audio_path=audio_path,
                    avatar_id=video.avatar_id,
                )
            else:
                # Use Kling for AI-generated video
                video_path = await video_gen.generate_ai_video(
                    prompt=f"Cinematic video about: {video.topic}. Style: {video.style}",
                    duration=min(video.duration_seconds, 10),  # Kling limit
                )

            video.video_raw_path = video_path
            video.status = VideoStatus.VIDEO_READY
            await db.commit()

            # Step 4: Add Subtitles
            video.status = VideoStatus.ADDING_SUBTITLES
            await db.commit()

            subtitle_gen = SubtitleGenerator()

            # Transcribe for accurate timing
            segments = await subtitle_gen.transcribe_audio(audio_path)

            # Generate ASS file with styling
            import os
            import uuid
            srt_path = os.path.join(settings.temp_dir, f"{uuid.uuid4()}.ass")
            subtitle_gen.segments_to_ass(segments, srt_path)

            video.subtitles_path = srt_path
            await db.commit()

            # Step 5: Final Render
            video.status = VideoStatus.RENDERING
            await db.commit()

            processor = VideoProcessor()

            # Burn subtitles
            final_path = await subtitle_gen.burn_subtitles(
                video_path=video_path,
                subtitle_path=srt_path,
            )

            # Generate thumbnail
            thumbnail_path = await processor.generate_thumbnail(final_path)

            video.video_final_path = final_path
            video.thumbnail_path = thumbnail_path
            video.status = VideoStatus.COMPLETED
            video.completed_at = datetime.utcnow()
            await db.commit()

            # Step 6: Auto-publish if requested
            if auto_publish and platforms:
                for platform in platforms:
                    try:
                        platform_enum = Platform(platform.lower())
                        task = PublishingTask(
                            video_id=video.id,
                            platform=platform_enum,
                            status=PublishingStatus.PENDING,
                        )
                        db.add(task)
                        await db.commit()
                        await db.refresh(task)
                        # Trigger publish task
                        publish_video_task.delay(task.id)
                    except ValueError:
                        continue

            return {"status": "success", "video_id": video.id}

        except Exception as e:
            video.status = VideoStatus.FAILED
            video.error_message = str(e)
            await db.commit()
            raise


@celery_app.task(bind=True, max_retries=3)
def publish_video_task(self, task_id: int):
    """Publish a video to a specific platform."""
    return run_async(_publish_video_task(task_id))


async def _publish_video_task(task_id: int):
    """Async implementation of publishing."""
    from app.services.publishers import (
        YouTubePublisher,
        TikTokPublisher,
        VKPublisher,
        TelegramPublisher,
        InstagramPublisher,
    )

    publishers = {
        Platform.YOUTUBE: YouTubePublisher(),
        Platform.TIKTOK: TikTokPublisher(),
        Platform.VK: VKPublisher(),
        Platform.TELEGRAM: TelegramPublisher(),
        Platform.INSTAGRAM: InstagramPublisher(),
    }

    async with async_session_maker() as db:
        # Get task with video
        result = await db.execute(
            select(PublishingTask).where(PublishingTask.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Publishing task {task_id} not found")

        # Get video
        video_result = await db.execute(
            select(Video).where(Video.id == task.video_id)
        )
        video = video_result.scalar_one_or_none()

        if not video or not video.video_final_path:
            task.status = PublishingStatus.FAILED
            task.error_message = "Video not ready"
            await db.commit()
            raise ValueError("Video not ready for publishing")

        try:
            task.status = PublishingStatus.UPLOADING
            await db.commit()

            publisher = publishers.get(task.platform)
            if not publisher:
                raise ValueError(f"Unknown platform: {task.platform}")

            if not await publisher.is_configured():
                task.status = PublishingStatus.FAILED
                task.error_message = f"{task.platform.value} not configured"
                await db.commit()
                return

            # Publish
            result = await publisher.publish(
                video_path=video.video_final_path,
                title=task.custom_title or video.title,
                description=task.custom_description or video.description or "",
                hashtags=task.custom_hashtags or video.hashtags or [],
                thumbnail_path=video.thumbnail_path,
            )

            if result.success:
                task.status = PublishingStatus.PUBLISHED
                task.platform_video_id = result.platform_video_id
                task.platform_url = result.platform_url
                task.published_at = datetime.utcnow()
            else:
                task.status = PublishingStatus.FAILED
                task.error_message = result.error_message
                task.retry_count += 1

            await db.commit()
            return {"status": task.status.value, "url": result.platform_url}

        except Exception as e:
            task.status = PublishingStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1
            await db.commit()
            raise


@celery_app.task
def schedule_content_plan(plan_id: int):
    """Schedule content items for a content plan."""
    return run_async(_schedule_content_plan(plan_id))


async def _schedule_content_plan(plan_id: int):
    """Generate schedule items for the next week."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(ContentPlan).where(ContentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan or not plan.is_active:
            return

        # Get next 7 days
        today = datetime.utcnow().date()
        items_created = 0

        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            weekday = current_date.weekday()

            # Check if this day is in publish_days
            if weekday not in plan.publish_days:
                continue

            # Check if item already exists for this date
            scheduled_datetime = datetime.combine(
                current_date, plan.publish_time
            )

            existing = await db.execute(
                select(ContentPlanItem).where(
                    ContentPlanItem.plan_id == plan_id,
                    ContentPlanItem.scheduled_date == scheduled_datetime,
                )
            )

            if existing.scalar_one_or_none():
                continue

            # Select topic (rotate through topics list)
            topic_index = items_created % len(plan.topics) if plan.topics else 0
            topic = plan.topics[topic_index] if plan.topics else plan.niche

            # Create schedule item
            item = ContentPlanItem(
                plan_id=plan_id,
                topic=topic,
                scheduled_date=scheduled_datetime,
            )
            db.add(item)
            items_created += 1

        await db.commit()
        return {"items_created": items_created}


@celery_app.task
def generate_scheduled_videos():
    """Generate videos for scheduled items that are due."""
    return run_async(_generate_scheduled_videos())


async def _generate_scheduled_videos():
    """Generate videos for items scheduled within the next 24 hours."""
    async with async_session_maker() as db:
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)

        # Find items that need video generation
        result = await db.execute(
            select(ContentPlanItem)
            .join(ContentPlan)
            .where(
                ContentPlanItem.is_generated == False,
                ContentPlanItem.scheduled_date <= tomorrow,
                ContentPlan.is_active == True,
            )
        )
        items = result.scalars().all()

        generated = 0
        for item in items:
            # Get parent plan
            plan_result = await db.execute(
                select(ContentPlan).where(ContentPlan.id == item.plan_id)
            )
            plan = plan_result.scalar_one_or_none()

            if not plan:
                continue

            # Create video
            video = Video(
                title=f"Video about {item.topic}",
                topic=item.topic,
                niche=plan.niche,
                style=plan.style,
                video_type=VideoType(plan.video_type),
                duration_seconds=plan.duration_seconds,
                voice_id=plan.voice_id,
                avatar_id=plan.avatar_id,
                scheduled_at=item.scheduled_date,
                is_auto_generated=True,
                status=VideoStatus.PENDING,
            )
            db.add(video)
            await db.commit()
            await db.refresh(video)

            # Link to plan item
            item.video_id = video.id
            item.is_generated = True
            await db.commit()

            # Trigger generation
            generate_video_pipeline.delay(
                video_id=video.id,
                auto_publish=False,  # Will be published by publish_scheduled_videos
                platforms=plan.platforms,
            )
            generated += 1

        return {"generated": generated}


@celery_app.task
def publish_scheduled_videos():
    """Publish videos that are scheduled and ready."""
    return run_async(_publish_scheduled_videos())


async def _publish_scheduled_videos():
    """Publish completed videos at their scheduled time."""
    async with async_session_maker() as db:
        now = datetime.utcnow()

        # Find ready videos that should be published
        result = await db.execute(
            select(ContentPlanItem)
            .join(ContentPlan)
            .where(
                ContentPlanItem.is_generated == True,
                ContentPlanItem.is_published == False,
                ContentPlanItem.scheduled_date <= now,
                ContentPlan.is_active == True,
            )
        )
        items = result.scalars().all()

        published = 0
        for item in items:
            if not item.video_id:
                continue

            # Check video is completed
            video_result = await db.execute(
                select(Video).where(Video.id == item.video_id)
            )
            video = video_result.scalar_one_or_none()

            if not video or video.status != VideoStatus.COMPLETED:
                continue

            # Get plan for platforms
            plan_result = await db.execute(
                select(ContentPlan).where(ContentPlan.id == item.plan_id)
            )
            plan = plan_result.scalar_one_or_none()

            if not plan:
                continue

            # Create publishing tasks
            for platform in plan.platforms:
                try:
                    platform_enum = Platform(platform.lower())

                    # Check if task exists
                    existing = await db.execute(
                        select(PublishingTask).where(
                            PublishingTask.video_id == video.id,
                            PublishingTask.platform == platform_enum,
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    task = PublishingTask(
                        video_id=video.id,
                        platform=platform_enum,
                        status=PublishingStatus.PENDING,
                    )
                    db.add(task)
                    await db.commit()
                    await db.refresh(task)

                    publish_video_task.delay(task.id)
                except ValueError:
                    continue

            item.is_published = True
            await db.commit()
            published += 1

        return {"published": published}


@celery_app.task
def process_scheduled_content():
    """Periodic task to process scheduled content."""
    # Re-schedule content plans
    run_async(_process_all_plans())


async def _process_all_plans():
    """Process all active content plans."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(ContentPlan).where(ContentPlan.is_active == True)
        )
        plans = result.scalars().all()

        for plan in plans:
            await _schedule_content_plan(plan.id)


@celery_app.task
def update_publishing_analytics():
    """Update analytics for published videos."""
    # TODO: Implement fetching stats from each platform's API
    pass


@celery_app.task
def generate_video_from_plan(plan_id: int):
    """Immediately generate a video from a content plan."""
    return run_async(_generate_video_from_plan(plan_id))


async def _generate_video_from_plan(plan_id: int):
    """Generate a single video from a content plan immediately."""
    async with async_session_maker() as db:
        result = await db.execute(
            select(ContentPlan).where(ContentPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise ValueError(f"Content plan {plan_id} not found")

        # Select a topic (use first one or niche)
        import random
        topic = random.choice(plan.topics) if plan.topics else plan.niche

        # Create video
        video = Video(
            title=f"Video about {topic}",
            topic=topic,
            niche=plan.niche,
            style=plan.style,
            video_type=VideoType(plan.video_type),
            duration_seconds=plan.duration_seconds,
            voice_id=plan.voice_id,
            avatar_id=plan.avatar_id,
            is_auto_generated=True,
            status=VideoStatus.PENDING,
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)

        # Trigger generation pipeline
        generate_video_pipeline.delay(
            video_id=video.id,
            auto_publish=True,
            platforms=plan.platforms,
        )

        return {"status": "ok", "video_id": video.id}
