"""add triage_rule table

Revision ID: a9c3e7d2f156
Revises: f2d9a6c1b834
Create Date: 2026-09-20 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a9c3e7d2f156'
down_revision: Union[str, Sequence[str], None] = 'f2d9a6c1b834'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

priority_enum = postgresql.ENUM(
    "baixa", "media", "alta", "critica", "vip", name="prioridadechamado", create_type=False
)
level_enum = postgresql.ENUM("n1", "n2", "n3", name="nivelatendimento", create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "triagerule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.Column("condition_category_id", sa.Integer(), nullable=True),
        sa.Column("condition_keyword", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("condition_outside_business_hours", sa.Boolean(), nullable=False),
        sa.Column("action_priority", priority_enum, nullable=True),
        sa.Column("action_team_id", sa.Integer(), nullable=True),
        sa.Column("action_level", level_enum, nullable=True),
        sa.ForeignKeyConstraint(["condition_category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["action_team_id"], ["team.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("triagerule")