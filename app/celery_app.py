from celery import Celery

from app.settings import settings
from app.services.logging import setup_logging

setup_logging()

celery_app = Celery(
    "svf",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    timezone=settings.TZ,
    enable_utc=False,
    task_default_queue="svf",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery_app.autodiscover_tasks(["app"])
