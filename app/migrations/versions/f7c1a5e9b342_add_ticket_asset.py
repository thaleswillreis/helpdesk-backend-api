"""add ticket_asset table

Revision ID: f7c1a5e9b342
Revises: e5b8f2d4a731
Create Date: 2026-09-25 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7c1a5e9b342"
down_revision: Union[str, Sequence[str], None] = "e5b8f2d4a731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ticketasset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("linked_by", sa.Integer(), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["asset.id"]),
        sa.ForeignKeyConstraint(["linked_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ticketasset_ticket_id"), "ticketasset", ["ticket_id"], unique=False
    )
    op.create_index(
        op.f("ix_ticketasset_asset_id"), "ticketasset", ["asset_id"], unique=False
    )
    op.create_unique_constraint(
        "uq_ticketasset_ticket_asset", "ticketasset", ["ticket_id", "asset_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_ticketasset_ticket_asset", "ticketasset", type_="unique")
    op.drop_index(op.f("ix_ticketasset_asset_id"), table_name="ticketasset")
    op.drop_index(op.f("ix_ticketasset_ticket_id"), table_name="ticketasset")
    op.drop_table("ticketasset")
