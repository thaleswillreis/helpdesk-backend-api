"""add sla_policy and team_schedule tables

Revision ID: d81a3f6e9c47
Revises: c9f4a7b2d156
Create Date: 2026-09-11 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd81a3f6e9c47'
down_revision: Union[str, Sequence[str], None] = 'c9f4a7b2d156'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

priority_enum = postgresql.ENUM(
    "baixa", "media", "alta", "critica", "vip",
    name="prioridadechamado",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "slapolicy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("response_time_minutes", sa.Integer(), nullable=False),
        sa.Column("resolution_time_minutes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_slapolicy_priority"), "slapolicy", ["priority"], unique=True)

    op.create_table(
        "teamschedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teamschedule_team_id"), "teamschedule", ["team_id"], unique=False)
    op.create_unique_constraint(
        "uq_teamschedule_team_weekday", "teamschedule", ["team_id", "weekday"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_teamschedule_team_weekday", "teamschedule", type_="unique")
    op.drop_index(op.f("ix_teamschedule_team_id"), table_name="teamschedule")
    op.drop_table("teamschedule")
    op.drop_index(op.f("ix_slapolicy_priority"), table_name="slapolicy")
    op.drop_table("slapolicy")