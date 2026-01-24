import logging
from datetime import datetime
from uuid import UUID

from celery import chain

from app import crud
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import ArtifactKind, EpisodeStatus, StepName, StepStatus
from app.services import agents
from app.services.clip_stub import render_clip_stub
from app.services.storage import StorageClient
from app.settings import settings

logger = logging.getLogger(__name__)


def enqueue_chain(job_id: UUID, start_step: str = "object"):
    steps = {
        "object": [object_step, factpack_step, script_step, storyboard_step, clip_stub_step],
        "factpack": [factpack_step, script_step, storyboard_step, clip_stub_step],
        "script": [script_step, storyboard_step, clip_stub_step],
        "storyboard": [storyboard_step, clip_stub_step],
        "clip": [clip_stub_step],
    }
    if start_step not in steps:
        raise ValueError("unknown step")
    sigs = [task.s(str(job_id)) for task in steps[start_step]]
    chain(*sigs).apply_async()


def _start_step(session, job_id: UUID, step_name: StepName):
    crud.set_job_status(session, job_id, EpisodeStatus.running)
    attempt = crud.get_next_attempt(session, job_id, step_name)
    run = crud.create_step_run(
        session,
        job_id,
        step_name,
        attempt,
        StepStatus.running,
        started_at=datetime.utcnow(),
    )
    return run


def _finish_step(session, run_id: UUID, payload: dict = None):
    crud.update_step_run(
        session,
        run_id,
        StepStatus.done,
        finished_at=datetime.utcnow(),
        payload_json=payload,
    )


def _fail_step(session, run_id: UUID, error_text: str, payload: dict = None):
    crud.update_step_run(
        session,
        run_id,
        StepStatus.failed,
        finished_at=datetime.utcnow(),
        error_text=error_text,
        payload_json=payload,
    )


@celery_app.task(bind=True, max_retries=2)
def object_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.object)

        object_spec = agents.generate_object_spec(session, job_uuid)
        crud.update_job_fields(session, job_uuid, object_title=object_spec.object_title)

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.ObjectSpec,
            uri=None,
            content_type="application/json",
            bytes_count=None,
            meta_json=object_spec.model_dump(),
        )
        _finish_step(session, run.id, payload={"object_title": object_spec.object_title})
        return job_id
    except Exception as exc:
        if run:
            _fail_step(session, run.id, str(exc))
        if self.request.retries >= self.max_retries:
            crud.set_job_status(session, UUID(job_id), EpisodeStatus.quarantined)
            raise
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2)
def factpack_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.factpack)
        object_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ObjectSpec)
        if not object_art or not object_art.meta_json:
            raise ValueError("ObjectSpec not found")
        object_spec = agents.ObjectSpec.model_validate(object_art.meta_json)

        factpack = agents.generate_factpack(session, job_uuid, object_spec)
        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.FactPack,
            uri=None,
            content_type="application/json",
            bytes_count=None,
            meta_json=factpack.model_dump(),
        )
        _finish_step(session, run.id, payload={"facts": len(factpack.facts)})
        return job_id
    except Exception as exc:
        if run:
            _fail_step(session, run.id, str(exc))
        if self.request.retries >= self.max_retries:
            crud.set_job_status(session, UUID(job_id), EpisodeStatus.quarantined)
            raise
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2)
def script_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.script)

        object_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ObjectSpec)
        fact_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.FactPack)
        if not object_art or not object_art.meta_json:
            raise ValueError("ObjectSpec not found")
        if not fact_art or not fact_art.meta_json:
            raise ValueError("FactPack not found")

        object_spec = agents.ObjectSpec.model_validate(object_art.meta_json)
        factpack = agents.FactPack.model_validate(fact_art.meta_json)
        series = agents.select_series(session)

        script, verdict_json, style_payload, repeat_detected = agents.generate_script_spec(
            session,
            job_uuid,
            object_spec,
            factpack,
            series,
        )

        hook_digest, voiceover_digest = agents.compute_digests(script)
        similarity_hook = crud.compute_similarity(session, hook_digest, "hook_digest", job_uuid)
        similarity_voice = crud.compute_similarity(session, voiceover_digest, "voiceover_digest", job_uuid)
        similarity_object = crud.compute_similarity(session, object_spec.object_title, "object_title", job_uuid)
        threshold = settings.REPEAT_SIMILARITY_THRESHOLD
        repeat_detected = max(similarity_hook, similarity_voice, similarity_object) >= threshold

        crud.update_job_fields(
            session,
            job_uuid,
            object_title=object_spec.object_title,
            hook_digest=hook_digest,
            voiceover_digest=voiceover_digest,
            judge_json=verdict_json,
            style_lint_json=style_payload,
            repeat_detected=repeat_detected,
        )

        if repeat_detected:
            raise ValueError("repeat_detected")

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.ScriptSpec,
            uri=None,
            content_type="application/json",
            bytes_count=None,
            meta_json=script.model_dump(),
        )

        _finish_step(session, run.id, payload={"hook": script.hook})
        return job_id
    except Exception as exc:
        if run:
            _fail_step(session, run.id, str(exc))
        if self.request.retries >= self.max_retries:
            crud.set_job_status(session, UUID(job_id), EpisodeStatus.quarantined)
            raise
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2)
def storyboard_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.storyboard)
        object_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ObjectSpec)
        script_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ScriptSpec)
        if not object_art or not object_art.meta_json:
            raise ValueError("ObjectSpec not found")
        if not script_art or not script_art.meta_json:
            raise ValueError("ScriptSpec not found")

        object_spec = agents.ObjectSpec.model_validate(object_art.meta_json)
        script = agents.ScriptSpec.model_validate(script_art.meta_json)
        storyboard = agents.generate_storyboard(session, job_uuid, object_spec, script)

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.Storyboard,
            uri=None,
            content_type="application/json",
            bytes_count=None,
            meta_json=storyboard.model_dump(),
        )
        _finish_step(session, run.id)
        return job_id
    except Exception as exc:
        if run:
            _fail_step(session, run.id, str(exc))
        if self.request.retries >= self.max_retries:
            crud.set_job_status(session, UUID(job_id), EpisodeStatus.quarantined)
            raise
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2)
def clip_stub_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.clip)
        script_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ScriptSpec)
        if not script_art or not script_art.meta_json:
            raise ValueError("ScriptSpec not found")
        script = agents.ScriptSpec.model_validate(script_art.meta_json)

        output_path = f"/tmp/{job_id}.mp4"
        render_clip_stub(script.hook, script.on_screen_captions, output_path)

        storage = StorageClient()
        key = f"episodes/{job_id}/clip.mp4"
        bytes_count = storage.upload_file(output_path, settings.MINIO_BUCKET, key, "video/mp4")
        uri = f"s3://{settings.MINIO_BUCKET}/{key}"

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.Clip,
            uri=uri,
            content_type="video/mp4",
            bytes_count=bytes_count,
            meta_json={
                "duration_sec": 8,
                "resolution": "1080x1920",
                "hook": script.hook,
                "captions": script.on_screen_captions[:2],
            },
        )
        crud.set_job_status(session, job_uuid, EpisodeStatus.done)
        _finish_step(session, run.id)
        return job_id
    except Exception as exc:
        if run:
            _fail_step(session, run.id, str(exc))
        if self.request.retries >= self.max_retries:
            crud.set_job_status(session, UUID(job_id), EpisodeStatus.quarantined)
            raise
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()
