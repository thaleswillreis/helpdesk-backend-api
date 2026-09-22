"""add sla_notification_state table

Revision ID: d3f7a1c9e628
Revises: c8e2f5a9d047
Create Date: 2026-09-23 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "d3f7a1c9e628"
down_revision: Union[str, Sequence[str], None] = "c8e2f5a9d047"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "slanotificationstate",
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column(
            "response_last_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "resolution_last_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.PrimaryKeyConstraint("ticket_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("slanotificationstate")
