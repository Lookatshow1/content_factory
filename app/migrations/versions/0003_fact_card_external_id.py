"""fact card external id

Revision ID: 0003_fact_card_external_id
Revises: 0002_content_v3
Create Date: 2025-01-25 00:45:00

"""
from alembic import op
import sqlalchemy as sa

revision = "0003_fact_card_external_id"
down_revision = "0002_content_v3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fact_card", sa.Column("external_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_fact_card_external_id", "fact_card", ["external_id"])


def downgrade():
    op.drop_constraint("uq_fact_card_external_id", "fact_card", type_="unique")
    op.drop_column("fact_card", "external_id")
