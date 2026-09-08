"""add user.level and ticket.current_level

Revision ID: b7d3f9a2c5e8
Revises: a2c8e6f1b4d7
Create Date: 2026-09-09 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'b7d3f9a2c5e8'
down_revision: Union[str, Sequence[str], None] = 'a2c8e6f1b4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

level_enum = postgresql.ENUM("n1", "n2", "n3", name="nivelatendimento", create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    level_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("user", sa.Column("level", level_enum, nullable=True))
    op.add_column(
        "ticket",
        sa.Column("current_level", level_enum, nullable=False, server_default="n1"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ticket", "current_level")
    op.drop_column("user", "level")

    level_enum.drop(op.get_bind(), checkfirst=True)