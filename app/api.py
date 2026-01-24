from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.db import get_session
from app.schemas import (
    EpisodeJobDetail,
    FactBankList,
    JobsList,
    SeriesList,
)
from app.services.storage import StorageClient
from app.tasks.pipeline import enqueue_chain

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
        enqueue_chain(job_id, step_name)
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


@router.get("/series", response_model=SeriesList)
def list_series(session=Depends(get_session)):
    items = crud.list_series(session)
    return {"items": items}


@router.get("/fact_bank", response_model=FactBankList)
def list_fact_bank(limit: int = 50, session=Depends(get_session)):
    items = crud.list_fact_bank(session, limit=limit)
    return {"items": items}
