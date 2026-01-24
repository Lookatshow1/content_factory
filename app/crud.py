from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select, text

from app.models import (
    Artifact,
    ArtifactKind,
    BudgetLedger,
    ContentSeries,
    EpisodeJob,
    EpisodeStatus,
    FactBank,
    FactCard,
    PublishJob,
    PublishStatus,
    AppSetting,
    StepName,
    StepRun,
    StepStatus,
)


def create_episode_job(session, scheduled_for=None, pipeline_version="v3", topic_seed=None):
    job = EpisodeJob(
        scheduled_for=scheduled_for,
        status=EpisodeStatus.queued,
        pipeline_version=pipeline_version,
        topic_seed=topic_seed,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def set_job_status(session, job_id: UUID, status: EpisodeStatus):
    job = session.get(EpisodeJob, job_id)
    if not job:
        return None
    job.status = status
    session.commit()
    return job


def update_job_fields(
    session,
    job_id: UUID,
    object_title: Optional[str] = None,
    hook_digest: Optional[str] = None,
    voiceover_digest: Optional[str] = None,
    judge_json: Optional[dict] = None,
    style_lint_json: Optional[dict] = None,
    repeat_detected: Optional[bool] = None,
):
    job = session.get(EpisodeJob, job_id)
    if not job:
        return None
    if object_title is not None:
        job.object_title = object_title
    if hook_digest is not None:
        job.hook_digest = hook_digest
    if voiceover_digest is not None:
        job.voiceover_digest = voiceover_digest
    if judge_json is not None:
        job.judge_json = judge_json
    if style_lint_json is not None:
        job.style_lint_json = style_lint_json
    if repeat_detected is not None:
        job.repeat_detected = repeat_detected
    session.commit()
    return job


def get_next_attempt(session, job_id: UUID, step_name: StepName) -> int:
    stmt = select(func.max(StepRun.attempt)).where(
        StepRun.episode_job_id == job_id,
        StepRun.step_name == step_name,
    )
    last = session.execute(stmt).scalar()
    return (last or 0) + 1


def create_step_run(
    session,
    job_id: UUID,
    step_name: StepName,
    attempt: int,
    status: StepStatus,
    started_at: Optional[datetime] = None,
    payload_json: Optional[dict] = None,
):
    run = StepRun(
        episode_job_id=job_id,
        step_name=step_name,
        attempt=attempt,
        status=status,
        started_at=started_at,
        payload_json=payload_json,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def update_step_run(
    session,
    step_run_id: UUID,
    status: StepStatus,
    finished_at: Optional[datetime] = None,
    error_code: Optional[str] = None,
    error_text: Optional[str] = None,
    payload_json: Optional[dict] = None,
):
    run = session.get(StepRun, step_run_id)
    if not run:
        return None
    run.status = status
    run.finished_at = finished_at
    run.error_code = error_code
    run.error_text = error_text
    if payload_json is not None:
        run.payload_json = payload_json
    session.commit()
    return run


def create_artifact(
    session,
    job_id: UUID,
    kind: ArtifactKind,
    uri: Optional[str] = None,
    content_type: Optional[str] = None,
    bytes_count: Optional[int] = None,
    meta_json: Optional[dict] = None,
):
    artifact = Artifact(
        episode_job_id=job_id,
        kind=kind,
        uri=uri,
        content_type=content_type,
        bytes=bytes_count,
        meta_json=meta_json,
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def list_jobs(session, limit: int = 50) -> List[EpisodeJob]:
    stmt = select(EpisodeJob).order_by(EpisodeJob.created_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars())


def get_job(session, job_id: UUID) -> Optional[EpisodeJob]:
    return session.get(EpisodeJob, job_id)


def get_job_detail(session, job_id: UUID):
    job = session.get(EpisodeJob, job_id)
    if not job:
        return None
    step_runs = (
        session.execute(
            select(StepRun)
            .where(StepRun.episode_job_id == job_id)
            .order_by(StepRun.started_at.asc().nulls_last())
        )
        .scalars()
        .all()
    )
    artifacts = (
        session.execute(
            select(Artifact)
            .where(Artifact.episode_job_id == job_id)
            .order_by(Artifact.kind.asc())
        )
        .scalars()
        .all()
    )
    return job, step_runs, artifacts


def get_artifact(session, artifact_id: UUID) -> Optional[Artifact]:
    return session.get(Artifact, artifact_id)


def get_latest_artifact(session, job_id: UUID, kind: ArtifactKind) -> Optional[Artifact]:
    stmt = (
        select(Artifact)
        .where(Artifact.episode_job_id == job_id, Artifact.kind == kind)
        .order_by(Artifact.id.desc())
        .limit(1)
    )
    return session.execute(stmt).scalars().first()


def list_series(session) -> List[ContentSeries]:
    stmt = select(ContentSeries).order_by(ContentSeries.name.asc())
    return list(session.execute(stmt).scalars())


def list_fact_bank(session, limit: int = 50) -> List[FactBank]:
    stmt = select(FactBank).limit(limit)
    return list(session.execute(stmt).scalars())


def get_fact_bank_by_tags(session, tags: List[str], limit: int = 5) -> List[FactBank]:
    if not tags:
        return []
    stmt = (
        select(FactBank)
        .where(FactBank.tags.overlap(tags))
        .limit(limit)
    )
    return list(session.execute(stmt).scalars())


def get_fact_cards(session, domain: str, tags: List[str], limit: int = 10) -> List[FactCard]:
    stmt = select(FactCard).where(FactCard.domain == domain)
    if tags:
        stmt = stmt.where(FactCard.tags.overlap(tags))
    stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars())


def create_publish_job(
    session,
    job_id: UUID,
    platform: str,
    scheduled_for=None,
    payload_json: Optional[dict] = None,
):
    publish_job = PublishJob(
        episode_job_id=job_id,
        platform=platform,
        status=PublishStatus.pending,
        scheduled_for=scheduled_for,
        payload_json=payload_json,
    )
    session.add(publish_job)
    session.commit()
    session.refresh(publish_job)
    return publish_job


def list_publish_jobs(session, limit: int = 50) -> List[PublishJob]:
    stmt = select(PublishJob).order_by(PublishJob.created_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars())


def update_publish_job(session, publish_job_id: UUID, status: PublishStatus, payload_json=None, error_text=None):
    job = session.get(PublishJob, publish_job_id)
    if not job:
        return None
    job.status = status
    if payload_json is not None:
        job.payload_json = payload_json
    if error_text is not None:
        job.error_text = error_text
    session.commit()
    return job


def get_setting(session, key: str) -> Optional[AppSetting]:
    stmt = select(AppSetting).where(AppSetting.key == key)
    return session.execute(stmt).scalars().first()


def set_setting(session, key: str, value_json: dict):
    setting = get_setting(session, key)
    if setting:
        setting.value_json = value_json
    else:
        setting = AppSetting(key=key, value_json=value_json)
        session.add(setting)
    session.commit()
    session.refresh(setting)
    return setting


def create_budget_entry(
    session,
    job_id: Optional[UUID],
    provider: Optional[str],
    model: Optional[str],
    units: Optional[int],
    cost: Optional[float],
    meta_json: Optional[dict] = None,
):
    entry = BudgetLedger(
        episode_job_id=job_id,
        provider=provider,
        model=model,
        units=units,
        cost=cost,
        meta_json=meta_json,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def get_recent_jobs_for_similarity(session, job_id: UUID, limit: int = 50):
    stmt = (
        select(EpisodeJob)
        .where(EpisodeJob.id != job_id)
        .order_by(EpisodeJob.created_at.desc())
        .limit(limit)
    )
    return list(session.execute(stmt).scalars())


def compute_similarity(session, target: str, field: str, job_id: UUID, limit: int = 50) -> float:
    if not target:
        return 0.0
    sql = text(
        """
        select max(similarity(:target, value)) as max_sim
        from (
            select {field} as value
            from episode_job
            where id != :job_id
            and {field} is not null
            order by created_at desc
            limit :limit
        ) t
        """.format(field=field)
    )
    result = session.execute(sql, {"target": target, "job_id": str(job_id), "limit": limit}).scalar()
    return float(result or 0.0)
