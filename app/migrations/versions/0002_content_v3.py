"""content v3

Revision ID: 0002_content_v3
Revises: 0001_init
Create Date: 2025-01-25 00:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_content_v3"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE step_name ADD VALUE IF NOT EXISTS 'research'")
    op.execute("ALTER TYPE step_name ADD VALUE IF NOT EXISTS 'tts'")
    op.execute("ALTER TYPE step_name ADD VALUE IF NOT EXISTS 'captions'")
    op.execute("ALTER TYPE step_name ADD VALUE IF NOT EXISTS 'render_final'")
    op.execute("ALTER TYPE step_name ADD VALUE IF NOT EXISTS 'publish_outbox'")

    op.execute("ALTER TYPE artifact_kind ADD VALUE IF NOT EXISTS 'VoiceoverAudio'")
    op.execute("ALTER TYPE artifact_kind ADD VALUE IF NOT EXISTS 'CaptionsSRT'")
    op.execute("ALTER TYPE artifact_kind ADD VALUE IF NOT EXISTS 'CaptionsASS'")
    op.execute("ALTER TYPE artifact_kind ADD VALUE IF NOT EXISTS 'ClipFinal'")

    op.add_column("budget_ledger", sa.Column("meta_json", postgresql.JSONB(), nullable=True))

    op.create_table(
        "fact_card",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("claim_lines", postgresql.JSONB(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
    )
    op.create_index("ix_fact_card_domain", "fact_card", ["domain"])
    op.create_index("ix_fact_card_tags", "fact_card", ["tags"], postgresql_using="gin")

    op.create_table(
        "publish_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("episode_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episode_job.id"), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "uploading",
                "processing",
                "done",
                "failed",
                "manual_required",
                name="publish_status",
            ),
            nullable=False,
        ),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "app_setting",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(), nullable=False, unique=True),
        sa.Column("value_json", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )


def downgrade():
    op.drop_table("app_setting")
    op.drop_table("publish_job")
    op.drop_index("ix_fact_card_tags", table_name="fact_card")
    op.drop_index("ix_fact_card_domain", table_name="fact_card")
    op.drop_table("fact_card")
    op.drop_column("budget_ledger", "meta_json")
    op.execute("DROP TYPE IF EXISTS publish_status")
