import time
from datetime import datetime
from uuid import UUID

from app import crud
from app.db import SessionLocal
from app.services.media import probe_video
from app.services.storage import StorageClient
from app.settings import settings
from app.tasks.pipeline import enqueue_chain
from app.models import ArtifactKind


def main():
    session = SessionLocal()
    try:
        job = crud.create_episode_job(
            session,
            scheduled_for=datetime.utcnow(),
            pipeline_version=settings.PIPELINE_VERSION,
            topic_seed="smoke",
        )
        job_id = job.id
        enqueue_chain(job_id, "idea", pipeline_version=job.pipeline_version)
        print(f"job {job_id} queued")
    finally:
        session.close()

    deadline = time.time() + 600
    status = None
    while time.time() < deadline:
        session = SessionLocal()
        try:
            job = crud.get_job(session, job_id)
            status = job.status.value if job else "missing"
        finally:
            session.close()
        if status in ("done", "quarantined"):
            break
        time.sleep(5)

    if status != "done":
        raise SystemExit(f"job ended with status {status}")

    session = SessionLocal()
    try:
        clip = crud.get_latest_artifact(session, job_id, kind=ArtifactKind.ClipFinal)
        if not clip:
            raise SystemExit("ClipFinal not found")
        storage = StorageClient()
        local_path = f"/tmp/{job_id}_final.mp4"
        storage.download_file(clip.uri, local_path)
        info = probe_video(local_path)
        print(info)
    finally:
        session.close()


if __name__ == "__main__":
    main()
