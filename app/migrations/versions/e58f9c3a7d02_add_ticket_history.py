"""add ticket_history table

Revision ID: e58f9c3a7d02
Revises: d47e1a92c8b1
Create Date: 2026-09-06 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = 'e58f9c3a7d02'
down_revision: Union[str, Sequence[str], None] = 'd47e1a92c8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tickethistory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("old_value", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("new_value", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("comment", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("changed_by", sa.Integer(), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickethistory_ticket_id"), "tickethistory", ["ticket_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_tickethistory_ticket_id"), table_name="tickethistory")
    op.drop_table("tickethistory")