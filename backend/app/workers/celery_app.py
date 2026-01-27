"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "content_factory",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result settings
    result_expires=3600 * 24,  # 24 hours

    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,

    # Beat schedule for automated content generation
    beat_schedule={
        # Check for scheduled content every hour
        "check-scheduled-content": {
            "task": "app.workers.tasks.process_scheduled_content",
            "schedule": crontab(minute=0),  # Every hour
        },
        # Generate content according to plans
        "generate-scheduled-videos": {
            "task": "app.workers.tasks.generate_scheduled_videos",
            "schedule": crontab(hour=6, minute=0),  # Daily at 6 AM
        },
        # Publish scheduled videos
        "publish-scheduled-videos": {
            "task": "app.workers.tasks.publish_scheduled_videos",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
        },
        # Update analytics
        "update-analytics": {
            "task": "app.workers.tasks.update_publishing_analytics",
            "schedule": crontab(hour="*/6"),  # Every 6 hours
        },
    },
)
