"""add system_settings table (singleton row)

Revision ID: e2b6c9a4f731
Revises: d81a3f6e9c47
Create Date: 2026-09-12 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e2b6c9a4f731'
down_revision: Union[str, Sequence[str], None] = 'd81a3f6e9c47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "systemsettings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sla_at_risk_threshold_percent", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "INSERT INTO systemsettings (id, sla_at_risk_threshold_percent) VALUES (1, 80)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("systemsettings")