import logging
from datetime import datetime
from uuid import UUID

from celery import chain

from app import crud
from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import ArtifactKind, EpisodeStatus, StepName, StepStatus
from app.services import agents
from app.services.captions import generate_captions
from app.services.clip_stub import render_clip_stub
from app.services.media import probe_duration
from app.services.logging import log_event
from app.services.storage import StorageClient
from app.services.tts import TTSClient
from app.services.video_render import render_clip, validate_final_video
from app.tasks.publish import process_publish_job
from app.settings import settings

logger = logging.getLogger(__name__)


PIPELINES = {
    "v1": ["idea", "script", "storyboard", "clip"],
    "v2": ["idea", "research", "script", "storyboard", "clip"],
    "v3": ["idea", "research", "script", "storyboard", "tts", "captions", "render_final", "publish_outbox"],
}


def _allowed_versions():
    return [item.strip() for item in settings.PIPELINE_ALLOWED.split(",") if item.strip()]


def _resolve_version(version: str) -> str:
    if version in _allowed_versions():
        return version
    return "v3"


def enqueue_chain(job_id: UUID, start_step: str = "idea", pipeline_version: str = None):
    if start_step == "object":
        start_step = "idea"
    if start_step == "factpack":
        start_step = "research"
    session = SessionLocal()
    try:
        if pipeline_version is None:
            job = crud.get_job(session, job_id)
            pipeline_version = job.pipeline_version if job else settings.PIPELINE_VERSION
    finally:
        session.close()
    version = _resolve_version(pipeline_version or settings.PIPELINE_VERSION)
    steps = PIPELINES.get(version, PIPELINES["v3"])
    if start_step not in steps:
        raise ValueError("unknown step")
    start_index = steps.index(start_step)
    task_names = steps[start_index:]
    task_map = {
        "idea": idea_step,
        "research": research_step,
        "script": script_step,
        "storyboard": storyboard_step,
        "tts": tts_step,
        "captions": captions_step,
        "render_final": render_final_step,
        "publish_outbox": publish_outbox_step,
        "clip": clip_stub_step,
    }
    sigs = [task_map[name].s(str(job_id)) for name in task_names]
    chain(*sigs).apply_async()


def _start_step(session, job_id: UUID, step_name: StepName):
    if step_name != StepName.publish_outbox:
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


def _fail_step(session, run_id: UUID, error_text: str, payload: dict = None, error_code: str = None):
    crud.update_step_run(
        session,
        run_id,
        StepStatus.failed,
        finished_at=datetime.utcnow(),
        error_text=error_text,
        error_code=error_code,
        payload_json=payload,
    )


@celery_app.task(bind=True, max_retries=2)
def idea_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.idea)
        log_event(logger, "step_start", episode_job_id=job_id, step="idea")

        idea_spec = agents.generate_idea_spec(session, job_uuid)
        crud.update_job_fields(session, job_uuid, object_title=idea_spec.object_title)

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.IdeaSpec,
            uri=None,
            content_type="application/json",
            bytes_count=None,
            meta_json=idea_spec.model_dump(),
        )
        _finish_step(session, run.id, payload={"object_title": idea_spec.object_title})
        log_event(logger, "step_done", episode_job_id=job_id, step="idea")
        return job_id
    except Exception as exc:
        error_code = "FACTS_MISSING" if str(exc) == "FACTS_MISSING" else None
        if run:
            _fail_step(session, run.id, str(exc), error_code=error_code)
        if self.request.retries >= self.max_retries:
            crud.set_job_status(session, UUID(job_id), EpisodeStatus.quarantined)
            raise
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()


@celery_app.task(bind=True, max_retries=2)
def research_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.research)
        log_event(logger, "step_start", episode_job_id=job_id, step="research")
        idea_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.IdeaSpec)
        if not idea_art or not idea_art.meta_json:
            raise ValueError("IdeaSpec not found")
        idea_spec = agents.IdeaSpec.model_validate(idea_art.meta_json)

        factpack = agents.build_factpack(session, idea_spec)
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
        log_event(logger, "step_done", episode_job_id=job_id, step="research")
        return job_id
    except Exception as exc:
        error_code = "FACTS_MISSING" if str(exc) == "FACTS_MISSING" else None
        if run:
            _fail_step(session, run.id, str(exc), error_code=error_code)
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
        log_event(logger, "step_start", episode_job_id=job_id, step="script")

        job = crud.get_job(session, job_uuid)
        pipeline_version = job.pipeline_version if job else settings.PIPELINE_VERSION
        idea_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.IdeaSpec)
        fact_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.FactPack)
        if not idea_art or not idea_art.meta_json:
            raise ValueError("IdeaSpec not found")

        idea_spec = agents.IdeaSpec.model_validate(idea_art.meta_json)
        if not fact_art or not fact_art.meta_json:
            if pipeline_version == "v1":
                factpack = agents.FactPack(facts=[])
            else:
                raise ValueError("FactPack not found")
        else:
            factpack = agents.FactPack.model_validate(fact_art.meta_json)
        series = agents.select_series(session)

        script, verdict_json, style_payload, style_failed = agents.generate_script_spec(
            session,
            job_uuid,
            idea_spec,
            factpack,
            series,
        )

        hook_digest, voiceover_digest = agents.compute_digests(script)
        similarity_hook = crud.compute_similarity(session, hook_digest, "hook_digest", job_uuid)
        similarity_voice = crud.compute_similarity(session, voiceover_digest, "voiceover_digest", job_uuid)
        similarity_object = crud.compute_similarity(session, idea_spec.object_title, "object_title", job_uuid)
        threshold = settings.REPEAT_SIMILARITY_THRESHOLD
        repeat_detected = max(similarity_hook, similarity_voice, similarity_object) >= threshold

        crud.update_job_fields(
            session,
            job_uuid,
            object_title=idea_spec.object_title,
            hook_digest=hook_digest,
            voiceover_digest=voiceover_digest,
            judge_json=verdict_json,
            style_lint_json=style_payload,
            repeat_detected=repeat_detected,
        )

        if repeat_detected:
            raise ValueError("repeat_detected")
        if style_failed:
            raise ValueError("STYLE_GUARD")

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
        log_event(logger, "step_done", episode_job_id=job_id, step="script")
        return job_id
    except Exception as exc:
        error_code = None
        if str(exc) == "STYLE_GUARD":
            error_code = "STYLE_GUARD"
        if str(exc) == "repeat_detected":
            error_code = "REPEAT_DETECTED"
        if run:
            _fail_step(session, run.id, str(exc), error_code=error_code)
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
        log_event(logger, "step_start", episode_job_id=job_id, step="storyboard")
        idea_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.IdeaSpec)
        script_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ScriptSpec)
        if not idea_art or not idea_art.meta_json:
            raise ValueError("IdeaSpec not found")
        if not script_art or not script_art.meta_json:
            raise ValueError("ScriptSpec not found")

        idea_spec = agents.IdeaSpec.model_validate(idea_art.meta_json)
        script = agents.ScriptSpec.model_validate(script_art.meta_json)
        storyboard = agents.generate_storyboard(session, job_uuid, idea_spec, script)

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
        log_event(logger, "step_done", episode_job_id=job_id, step="storyboard")
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
def tts_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.tts)
        log_event(logger, "step_start", episode_job_id=job_id, step="tts")
        script_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ScriptSpec)
        if not script_art or not script_art.meta_json:
            raise ValueError("ScriptSpec not found")
        script = agents.ScriptSpec.model_validate(script_art.meta_json)

        tts = TTSClient(job_id=job_uuid)
        result = tts.synthesize(script.voiceover_text)
        audio_path = result["path"]
        duration = probe_duration(audio_path)

        storage = StorageClient()
        key = f"episodes/{job_id}/voiceover.wav"
        bytes_count = storage.upload_file(audio_path, settings.MINIO_BUCKET, key, "audio/wav")
        uri = f"s3://{settings.MINIO_BUCKET}/{key}"

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.VoiceoverAudio,
            uri=uri,
            content_type="audio/wav",
            bytes_count=bytes_count,
            meta_json={
                "duration_sec": duration,
                "provider": result.get("provider"),
                "voice_id": result.get("voice_id"),
            },
        )
        _finish_step(session, run.id, payload={"duration_sec": duration})
        log_event(logger, "step_done", episode_job_id=job_id, step="tts")
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
def captions_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.captions)
        log_event(logger, "step_start", episode_job_id=job_id, step="captions")
        script_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ScriptSpec)
        voice_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.VoiceoverAudio)
        if not script_art or not script_art.meta_json:
            raise ValueError("ScriptSpec not found")
        if not voice_art or not voice_art.uri:
            raise ValueError("VoiceoverAudio not found")
        script = agents.ScriptSpec.model_validate(script_art.meta_json)

        storage = StorageClient()
        audio_path = f"/tmp/{job_id}_voice.wav"
        storage.download_file(voice_art.uri, audio_path)

        srt_path, ass_path, duration = generate_captions(
            script.on_screen_captions,
            audio_path,
            f"/tmp/{job_id}_captions",
        )

        srt_key = f"episodes/{job_id}/captions.srt"
        ass_key = f"episodes/{job_id}/captions.ass"
        srt_bytes = storage.upload_file(srt_path, settings.MINIO_BUCKET, srt_key, "text/plain")
        ass_bytes = storage.upload_file(ass_path, settings.MINIO_BUCKET, ass_key, "text/plain")

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.CaptionsSRT,
            uri=f"s3://{settings.MINIO_BUCKET}/{srt_key}",
            content_type="text/plain",
            bytes_count=srt_bytes,
            meta_json={"duration_sec": duration},
        )
        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.CaptionsASS,
            uri=f"s3://{settings.MINIO_BUCKET}/{ass_key}",
            content_type="text/plain",
            bytes_count=ass_bytes,
            meta_json={"duration_sec": duration},
        )
        _finish_step(session, run.id, payload={"duration_sec": duration})
        log_event(logger, "step_done", episode_job_id=job_id, step="captions")
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
def render_final_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.render_final)
        log_event(logger, "step_start", episode_job_id=job_id, step="render_final")
        script_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.ScriptSpec)
        voice_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.VoiceoverAudio)
        ass_art = crud.get_latest_artifact(session, job_uuid, ArtifactKind.CaptionsASS)
        if not script_art or not script_art.meta_json:
            raise ValueError("ScriptSpec not found")
        if not voice_art or not voice_art.uri:
            raise ValueError("VoiceoverAudio not found")
        if not ass_art or not ass_art.uri:
            raise ValueError("CaptionsASS not found")

        script = agents.ScriptSpec.model_validate(script_art.meta_json)
        storage = StorageClient()
        voice_path = f"/tmp/{job_id}_voice.wav"
        ass_path = f"/tmp/{job_id}.ass"
        storage.download_file(voice_art.uri, voice_path)
        storage.download_file(ass_art.uri, ass_path)

        output_path = f"/tmp/{job_id}_final.mp4"
        if settings.VIDEO_BACKEND == "heygen" and settings.HEYGEN_API_KEY:
            crud.update_step_run(
                session,
                run.id,
                StepStatus.running,
                payload_json={"status": "render_pending"},
            )
        render_clip(str(job_id), script.hook, ass_path, voice_path, output_path)
        info = validate_final_video(output_path)

        key = f"episodes/{job_id}/clip_final.mp4"
        bytes_count = storage.upload_file(output_path, settings.MINIO_BUCKET, key, "video/mp4")
        uri = f"s3://{settings.MINIO_BUCKET}/{key}"

        crud.create_artifact(
            session,
            job_uuid,
            ArtifactKind.ClipFinal,
            uri=uri,
            content_type="video/mp4",
            bytes_count=bytes_count,
            meta_json={
                "resolution": f"{info.get('width')}x{info.get('height')}",
                "video_codec": info.get("video_codec"),
                "audio_codec": info.get("audio_codec"),
                "hook": script.hook,
            },
        )
        crud.set_job_status(session, job_uuid, EpisodeStatus.done)
        _finish_step(session, run.id)
        log_event(logger, "step_done", episode_job_id=job_id, step="render_final")
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
def publish_outbox_step(self, job_id: str):
    session = SessionLocal()
    run = None
    try:
        job_uuid = UUID(job_id)
        run = _start_step(session, job_uuid, StepName.publish_outbox)
        log_event(logger, "step_start", episode_job_id=job_id, step="publish_outbox")
        platforms = []
        if settings.PUBLISH_VK_ENABLED:
            platforms.append("vk")
        if settings.PUBLISH_TIKTOK_ENABLED:
            platforms.append("tiktok")
        created = []
        for platform in platforms:
            publish_job = crud.create_publish_job(session, job_uuid, platform)
            created.append(str(publish_job.id))
            process_publish_job.delay(str(publish_job.id))
        _finish_step(session, run.id, payload={"publish_jobs": created})
        log_event(logger, "step_done", episode_job_id=job_id, step="publish_outbox")
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
        log_event(logger, "step_start", episode_job_id=job_id, step="clip")
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
        log_event(logger, "step_done", episode_job_id=job_id, step="clip")
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
