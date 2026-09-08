"""add team, team_membership, and ticket.team_id

Revision ID: f6a1d84b2e93
Revises: e58f9c3a7d02
Create Date: 2026-09-07 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = 'f6a1d84b2e93'
down_revision: Union[str, Sequence[str], None] = 'e58f9c3a7d02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_team_name"), "team", ["name"], unique=True)

    op.create_table(
        "teammembership",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("team_id", "user_id"),
    )

    op.add_column("ticket", sa.Column("team_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_ticket_team_id", "ticket", "team", ["team_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_ticket_team_id", "ticket", type_="foreignkey")
    op.drop_column("ticket", "team_id")

    op.drop_table("teammembership")

    op.drop_index(op.f("ix_team_name"), table_name="team")
    op.drop_table("team")