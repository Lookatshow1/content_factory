import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class EpisodeStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    quarantined = "quarantined"


class StepName(str, enum.Enum):
    idea = "idea"
    object = "object"
    research = "research"
    factpack = "factpack"
    script = "script"
    storyboard = "storyboard"
    tts = "tts"
    captions = "captions"
    render_final = "render_final"
    publish_outbox = "publish_outbox"
    clip = "clip"


class StepStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class ArtifactKind(str, enum.Enum):
    ObjectSpec = "ObjectSpec"
    IdeaSpec = "IdeaSpec"
    FactPack = "FactPack"
    ScriptSpec = "ScriptSpec"
    Storyboard = "Storyboard"
    VoiceoverAudio = "VoiceoverAudio"
    CaptionsSRT = "CaptionsSRT"
    CaptionsASS = "CaptionsASS"
    Clip = "Clip"
    ClipFinal = "ClipFinal"


class EpisodeJob(Base):
    __tablename__ = "episode_job"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(EpisodeStatus, name="episode_status"), default=EpisodeStatus.queued)
    pipeline_version = Column(String, default="v3")
    topic_seed = Column(String, nullable=True)

    object_title = Column(String, nullable=True)
    hook_digest = Column(String, nullable=True)
    voiceover_digest = Column(String, nullable=True)
    judge_json = Column(JSONB, nullable=True)
    style_lint_json = Column(JSONB, nullable=True)
    repeat_detected = Column(Boolean, default=False)

    step_runs = relationship("StepRun", back_populates="episode_job", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="episode_job", cascade="all, delete-orphan")
    budget_entries = relationship("BudgetLedger", back_populates="episode_job", cascade="all, delete-orphan")


class StepRun(Base):
    __tablename__ = "step_run"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_job_id = Column(UUID(as_uuid=True), ForeignKey("episode_job.id"), nullable=False)
    step_name = Column(Enum(StepName, name="step_name"), nullable=False)
    attempt = Column(Integer, default=1)
    status = Column(Enum(StepStatus, name="step_status"), default=StepStatus.queued)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String, nullable=True)
    error_text = Column(Text, nullable=True)
    payload_json = Column(JSONB, nullable=True)

    episode_job = relationship("EpisodeJob", back_populates="step_runs")


class Artifact(Base):
    __tablename__ = "artifact"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_job_id = Column(UUID(as_uuid=True), ForeignKey("episode_job.id"), nullable=False)
    kind = Column(Enum(ArtifactKind, name="artifact_kind"), nullable=False)
    uri = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    bytes = Column(Integer, nullable=True)
    meta_json = Column(JSONB, nullable=True)

    episode_job = relationship("EpisodeJob", back_populates="artifacts")


class BudgetLedger(Base):
    __tablename__ = "budget_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_job_id = Column(UUID(as_uuid=True), ForeignKey("episode_job.id"), nullable=True)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    units = Column(Integer, nullable=True)
    cost = Column(Numeric, nullable=True)
    meta_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    episode_job = relationship("EpisodeJob", back_populates="budget_entries")


class ContentSeries(Base):
    __tablename__ = "content_series"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    prompt_preamble = Column(Text, nullable=True)
    weights_json = Column(JSONB, nullable=True)
    rules_json = Column(JSONB, nullable=True)


class FactBank(Base):
    __tablename__ = "fact_bank"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim = Column(Text, nullable=False)
    source_title = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    source_locator = Column(String, nullable=True)
    evidence_snippet = Column(String, nullable=True)
    reliability = Column(String, nullable=True)
    tags = Column(ARRAY(String), nullable=True)


class FactCard(Base):
    __tablename__ = "fact_card"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String, nullable=True, unique=True)
    domain = Column(String, nullable=False)
    title = Column(String, nullable=False)
    claim_lines = Column(JSONB, nullable=False)
    sources = Column(JSONB, nullable=False)
    tags = Column(ARRAY(String), nullable=True)
    language = Column(String, default="ru")


class PublishStatus(str, enum.Enum):
    pending = "pending"
    uploading = "uploading"
    processing = "processing"
    done = "done"
    failed = "failed"
    manual_required = "manual_required"


class PublishJob(Base):
    __tablename__ = "publish_job"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_job_id = Column(UUID(as_uuid=True), ForeignKey("episode_job.id"), nullable=False)
    platform = Column(String, nullable=False)
    status = Column(Enum(PublishStatus, name="publish_status"), default=PublishStatus.pending)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    payload_json = Column(JSONB, nullable=True)
    error_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    episode_job = relationship("EpisodeJob")


class Setting(Base):
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, nullable=False, unique=True)
    value_json = Column(JSONB, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
