import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app import crud
from app.db import SessionLocal
from app.tasks.pipeline import enqueue_chain
from app.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_times(times: str):
    result = []
    for part in (times or "").split(","):
        part = part.strip()
        if not part:
            continue
        hour, minute = part.split(":")
        result.append((int(hour), int(minute)))
    return result


def create_episode_job():
    session = SessionLocal()
    try:
        now = datetime.now(ZoneInfo(settings.TZ))
        job = crud.create_episode_job(session, scheduled_for=now, topic_seed=now.isoformat())
        enqueue_chain(job.id, "object")
        logger.info("scheduled job %s", job.id)
    finally:
        session.close()


def main():
    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.TZ))
    for hour, minute in _parse_times(settings.RUN_TIMES):
        trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.add_job(create_episode_job, trigger)
        logger.info("registered schedule at %02d:%02d", hour, minute)
    scheduler.start()


if __name__ == "__main__":
    main()
