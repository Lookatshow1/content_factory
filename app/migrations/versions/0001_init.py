"""init

Revision ID: 0001_init
Revises: 
Create Date: 2025-01-25 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "episode_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("queued", "running", "done", "quarantined", name="episode_status"), nullable=False),
        sa.Column("pipeline_version", sa.String(), nullable=True),
        sa.Column("topic_seed", sa.String(), nullable=True),
        sa.Column("object_title", sa.String(), nullable=True),
        sa.Column("hook_digest", sa.String(), nullable=True),
        sa.Column("voiceover_digest", sa.String(), nullable=True),
        sa.Column("judge_json", postgresql.JSONB(), nullable=True),
        sa.Column("style_lint_json", postgresql.JSONB(), nullable=True),
        sa.Column("repeat_detected", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    op.create_table(
        "step_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("episode_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episode_job.id"), nullable=False),
        sa.Column("step_name", sa.Enum("object", "factpack", "script", "storyboard", "clip", "idea", name="step_name"), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("queued", "running", "done", "failed", name="step_status"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "artifact",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("episode_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episode_job.id"), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "ObjectSpec",
                "FactPack",
                "ScriptSpec",
                "Storyboard",
                "Clip",
                "IdeaSpec",
                name="artifact_kind",
            ),
            nullable=False,
        ),
        sa.Column("uri", sa.String(), nullable=True),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("bytes", sa.Integer(), nullable=True),
        sa.Column("meta_json", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "budget_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("episode_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episode_job.id"), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("units", sa.Integer(), nullable=True),
        sa.Column("cost", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "content_series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("prompt_preamble", sa.Text(), nullable=True),
        sa.Column("weights_json", postgresql.JSONB(), nullable=True),
        sa.Column("rules_json", postgresql.JSONB(), nullable=True),
    )

    op.create_table(
        "fact_bank",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("source_title", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("source_locator", sa.String(), nullable=True),
        sa.Column("evidence_snippet", sa.String(), nullable=True),
        sa.Column("reliability", sa.String(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade():
    op.drop_table("fact_bank")
    op.drop_table("content_series")
    op.drop_table("budget_ledger")
    op.drop_table("artifact")
    op.drop_table("step_run")
    op.drop_table("episode_job")
    op.execute("DROP TYPE IF EXISTS artifact_kind")
    op.execute("DROP TYPE IF EXISTS step_status")
    op.execute("DROP TYPE IF EXISTS step_name")
    op.execute("DROP TYPE IF EXISTS episode_status")
