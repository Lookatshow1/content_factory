"""settings table and trgm indexes

Revision ID: 0004_settings_and_indexes
Revises: 0003_fact_card_external_id
Create Date: 2025-01-25 01:10:00

"""
from alembic import op
import sqlalchemy as sa

revision = "0004_settings_and_indexes"
down_revision = "0003_fact_card_external_id"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("app_setting", "settings")

    op.execute("UPDATE episode_job SET pipeline_version='v3' WHERE pipeline_version IS NULL")
    op.alter_column(
        "episode_job",
        "pipeline_version",
        existing_type=sa.String(),
        server_default="v3",
        existing_nullable=True,
    )

    op.create_index(
        "ix_episode_job_hook_digest_trgm",
        "episode_job",
        ["hook_digest"],
        postgresql_using="gin",
        postgresql_ops={"hook_digest": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_episode_job_voiceover_digest_trgm",
        "episode_job",
        ["voiceover_digest"],
        postgresql_using="gin",
        postgresql_ops={"voiceover_digest": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_episode_job_object_title_trgm",
        "episode_job",
        ["object_title"],
        postgresql_using="gin",
        postgresql_ops={"object_title": "gin_trgm_ops"},
    )


def downgrade():
    op.drop_index("ix_episode_job_object_title_trgm", table_name="episode_job")
    op.drop_index("ix_episode_job_voiceover_digest_trgm", table_name="episode_job")
    op.drop_index("ix_episode_job_hook_digest_trgm", table_name="episode_job")

    op.alter_column(
        "episode_job",
        "pipeline_version",
        existing_type=sa.String(),
        server_default=None,
        existing_nullable=True,
    )
    op.rename_table("settings", "app_setting")
