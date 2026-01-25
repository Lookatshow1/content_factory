from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StepRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_job_id: UUID
    step_name: str
    attempt: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_code: Optional[str]
    error_text: Optional[str]
    payload_json: Optional[dict]


class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_job_id: UUID
    kind: str
    uri: Optional[str]
    content_type: Optional[str]
    bytes: Optional[int]
    meta_json: Optional[dict]


class EpisodeJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    scheduled_for: Optional[datetime]
    status: str
    pipeline_version: Optional[str]
    topic_seed: Optional[str]
    object_title: Optional[str]
    repeat_detected: Optional[bool]


class EpisodeJobDetail(EpisodeJobOut):
    judge_json: Optional[dict]
    style_lint_json: Optional[dict]
    step_runs: List[StepRunOut] = []
    artifacts: List[ArtifactOut] = []


class ContentSeriesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    prompt_preamble: Optional[str]
    weights_json: Optional[dict]
    rules_json: Optional[dict]


class FactBankOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim: str
    source_title: str
    source_url: Optional[str]
    source_locator: Optional[str]
    evidence_snippet: Optional[str]
    reliability: Optional[str]
    tags: Optional[List[str]]


class JobsList(BaseModel):
    items: List[EpisodeJobOut]


class SeriesList(BaseModel):
    items: List[ContentSeriesOut]


class FactBankList(BaseModel):
    items: List[FactBankOut]


class PublishJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_job_id: UUID
    platform: str
    status: str
    scheduled_for: Optional[datetime]
    payload_json: Optional[dict]
    error_text: Optional[str]
    created_at: datetime


class PublishJobsList(BaseModel):
    items: List[PublishJobOut]
