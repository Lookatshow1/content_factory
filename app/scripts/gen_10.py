import argparse
import time
from collections import Counter
from datetime import datetime

from app import crud
from app.db import SessionLocal
from app.models import EpisodeStatus
from app.settings import settings
from app.tasks.pipeline import enqueue_chain


def wait_job(job_id, timeout_sec: int = 900):
    deadline = time.time() + timeout_sec
    status = None
    while time.time() < deadline:
        session = SessionLocal()
        try:
            job = crud.get_job(session, job_id)
            status = job.status.value if job else "missing"
        finally:
            session.close()
        if status in ("done", "quarantined"):
            return status
        time.sleep(5)
    return status or "timeout"


def classify_quarantine(step_runs):
    for run in step_runs:
        if run.status.value != "failed":
            continue
        code = (run.error_code or "").upper()
        text = (run.error_text or "").upper()
        if "FACTS_MISSING" in code or "FACTS_MISSING" in text:
            return "FACTS_MISSING"
        if "STYLE_GUARD" in code or "STYLE_GUARD" in text:
            return "STYLE_GUARD"
        if "VALIDATION" in code or "VALIDATION" in text:
            return "VALIDATION"
        if "TTS_EMPTY" in code or "TTS_EMPTY" in text:
            return "TTS_EMPTY"
    return "OTHER"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    stats = Counter()
    for idx in range(args.count):
        session = SessionLocal()
        try:
            job = crud.create_episode_job(
                session,
                scheduled_for=datetime.utcnow(),
                pipeline_version=settings.PIPELINE_VERSION,
                topic_seed=f"gen_10_{idx}",
            )
            job_id = job.id
            enqueue_chain(job_id, "idea", pipeline_version=job.pipeline_version)
            print(f"job_id={job_id}")
        finally:
            session.close()

        status = wait_job(job_id, timeout_sec=args.timeout)
        stats[status] += 1
        if status == "quarantined":
            session = SessionLocal()
            try:
                detail = crud.get_job_detail(session, job_id)
                if detail:
                    _, step_runs, _ = detail
                    reason = classify_quarantine(step_runs)
                    stats[reason] += 1
                    print(f"quarantine_reason={reason}")
            finally:
                session.close()

    print("stats", dict(stats))


if __name__ == "__main__":
    main()
