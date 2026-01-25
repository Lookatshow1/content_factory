from uuid import UUID
from typing import Optional

import shutil
from datetime import datetime

import redis
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app import crud
from app.db import get_session
from app.models import EpisodeJob, StepRun, ArtifactKind
from app.schemas import (
    EpisodeJobDetail,
    FactBankList,
    JobsList,
    PublishJobsList,
    SeriesList,
)
from app.services.storage import StorageClient
from app.tasks.pipeline import enqueue_chain
from app.settings import settings

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/jobs", response_model=JobsList)
def list_jobs(limit: int = 50, session=Depends(get_session)):
    jobs = crud.list_jobs(session, limit=limit)
    return {"items": jobs}


@router.get("/jobs/{job_id}", response_model=EpisodeJobDetail)
def job_detail(job_id: UUID, session=Depends(get_session)):
    result = crud.get_job_detail(session, job_id)
    if not result:
        raise HTTPException(status_code=404, detail="job not found")
    job, step_runs, artifacts = result
    return EpisodeJobDetail(
        id=job.id,
        created_at=job.created_at,
        scheduled_for=job.scheduled_for,
        status=job.status,
        pipeline_version=job.pipeline_version,
        topic_seed=job.topic_seed,
        object_title=job.object_title,
        repeat_detected=job.repeat_detected,
        judge_json=job.judge_json,
        style_lint_json=job.style_lint_json,
        step_runs=step_runs,
        artifacts=artifacts,
    )


@router.post("/jobs/{job_id}/rerun/{step_name}")
def rerun(job_id: UUID, step_name: str, session=Depends(get_session)):
    job = crud.get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    try:
        enqueue_chain(job_id, step_name, pipeline_version=job.pipeline_version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "queued", "job_id": str(job_id), "from_step": step_name}


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: UUID, session=Depends(get_session)):
    artifact = crud.get_artifact(session, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact not found")
    if not artifact.uri:
        raise HTTPException(status_code=400, detail="artifact has no uri")
    storage = StorageClient()
    url = storage.presign_url(artifact.uri, expires_in=900)
    return {"url": url}


@router.get("/download")
def download_latest(job_id: Optional[UUID] = None, artifact_id: Optional[UUID] = None, session=Depends(get_session)):
    if artifact_id:
        artifact = crud.get_artifact(session, artifact_id)
        if not artifact:
            raise HTTPException(status_code=404, detail="artifact not found")
    else:
        if job_id:
            artifact = crud.get_latest_artifact(session, job_id, kind=ArtifactKind.ClipFinal)
        else:
            jobs = crud.list_jobs(session, limit=1)
            if not jobs:
                raise HTTPException(status_code=404, detail="no jobs")
            artifact = crud.get_latest_artifact(session, jobs[0].id, kind=ArtifactKind.ClipFinal)
        if not artifact:
            raise HTTPException(status_code=404, detail="ClipFinal not found")
    if not artifact.uri:
        raise HTTPException(status_code=400, detail="artifact has no uri")

    storage = StorageClient()
    obj = storage.get_object_stream(artifact.uri)
    body = obj["Body"]
    content_type = obj.get("ContentType") or artifact.content_type or "application/octet-stream"
    content_length = obj.get("ContentLength")
    filename = f"clip_{artifact.episode_job_id}.mp4"

    def _iter():
        try:
            for chunk in body.iter_chunks(chunk_size=1024 * 1024):
                if chunk:
                    yield chunk
        finally:
            body.close()

    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    if content_length:
        headers["Content-Length"] = str(content_length)
    return StreamingResponse(_iter(), media_type=content_type, headers=headers)


@router.get("/series", response_model=SeriesList)
def list_series(session=Depends(get_session)):
    items = crud.list_series(session)
    return {"items": items}


@router.get("/fact_bank", response_model=FactBankList)
def list_fact_bank(limit: int = 50, session=Depends(get_session)):
    items = crud.list_fact_bank(session, limit=limit)
    return {"items": items}


@router.get("/publish/jobs", response_model=PublishJobsList)
def list_publish_jobs(limit: int = 50, session=Depends(get_session)):
    items = crud.list_publish_jobs(session, limit=limit)
    return {"items": items}


@router.get("/admin/health")
def admin_health(session=Depends(get_session)):
    db_ok = False
    redis_ok = False
    minio_ok = False
    try:
        session.execute(select(func.now()))
        db_ok = True
    except Exception:
        db_ok = False
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_ok = redis_client.ping()
    except Exception:
        redis_ok = False
    try:
        storage = StorageClient()
        storage.ensure_bucket(settings.MINIO_BUCKET)
        minio_ok = True
    except Exception:
        minio_ok = False

    disk = shutil.disk_usage("/")
    return {
        "db": db_ok,
        "redis": redis_ok,
        "minio": minio_ok,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/admin/metrics")
def admin_metrics(session=Depends(get_session)):
    job_counts = session.execute(
        select(EpisodeJob.status, func.count()).group_by(EpisodeJob.status)
    ).all()
    status_counts = {status.value: count for status, count in job_counts}

    step_avg = session.execute(
        select(
            StepRun.step_name,
            func.avg(func.extract("epoch", StepRun.finished_at - StepRun.started_at)),
        ).where(StepRun.finished_at.isnot(None))
        .group_by(StepRun.step_name)
    ).all()
    avg_step_duration = {name.value: round(value or 0, 2) for name, value in step_avg}

    total = sum(status_counts.values()) or 1
    quarantined = status_counts.get("quarantined", 0)
    return {
        "job_counts": status_counts,
        "avg_step_duration_sec": avg_step_duration,
        "quarantined_pct": round(quarantined / total * 100, 2),
    }
