from uuid import UUID

from app import crud
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import ArtifactKind, PublishJob, PublishStatus
from app.services.publish.tiktok import publish_to_tiktok
from app.services.publish.vk import publish_to_vk
from app.services.storage import StorageClient


@celery_app.task(bind=True, max_retries=2)
def process_publish_job(self, publish_job_id: str):
    session = SessionLocal()
    try:
        job = session.get(PublishJob, UUID(publish_job_id))
        if not job:
            return publish_job_id
        if job.status in (PublishStatus.done, PublishStatus.manual_required):
            return publish_job_id
        job = crud.update_publish_job(session, UUID(publish_job_id), PublishStatus.uploading)
        if not job:
            return publish_job_id

        clip_art = crud.get_latest_artifact(session, job.episode_job_id, ArtifactKind.ClipFinal)
        if not clip_art or not clip_art.uri:
            raise ValueError("ClipFinal not found")

        storage = StorageClient()
        local_path = f"/tmp/publish_{publish_job_id}.mp4"
        storage.download_file(clip_art.uri, local_path)

        if job.platform == "vk":
            result = publish_to_vk(local_path, "short-video-factory", "Автогенерируемый выпуск")
            crud.update_publish_job(session, job.id, PublishStatus.done, payload_json=result)
        elif job.platform == "tiktok":
            result = publish_to_tiktok(local_path, "short-video-factory")
            crud.update_publish_job(session, job.id, PublishStatus.manual_required, payload_json=result)
        else:
            crud.update_publish_job(session, job.id, PublishStatus.failed, error_text="unknown platform")
        return publish_job_id
    except Exception as exc:
        crud.update_publish_job(session, UUID(publish_job_id), PublishStatus.failed, error_text=str(exc))
        raise
    finally:
        session.close()
