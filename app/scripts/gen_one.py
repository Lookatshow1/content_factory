import argparse
import time
from datetime import datetime

from app import crud
from app.db import SessionLocal
from app.models import ArtifactKind, EpisodeStatus
from app.services.storage import StorageClient
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", default="", help="path to save ClipFinal")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    session = SessionLocal()
    try:
        job = crud.create_episode_job(
            session,
            scheduled_for=datetime.utcnow(),
            pipeline_version=settings.PIPELINE_VERSION,
            topic_seed="gen_one",
        )
        job_id = job.id
        enqueue_chain(job_id, "idea", pipeline_version=job.pipeline_version)
        print(f"job_id={job_id}")
    finally:
        session.close()

    status = wait_job(job_id, timeout_sec=args.timeout)
    print(f"status={status}")
    if status != "done":
        raise SystemExit(1)

    session = SessionLocal()
    try:
        clip = crud.get_latest_artifact(session, job_id, kind=ArtifactKind.ClipFinal)
        if not clip:
            raise SystemExit("ClipFinal not found")
        storage = StorageClient()
        url = storage.presign_url(clip.uri, expires_in=900)
        print(f"clip_url={url}")
        if args.download:
            storage.download_file(clip.uri, args.download)
            print(f"downloaded={args.download}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
