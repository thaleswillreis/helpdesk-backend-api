"""add category.default_team_id

Revision ID: a2c8e6f1b4d7
Revises: f6a1d84b2e93
Create Date: 2026-09-08 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a2c8e6f1b4d7'
down_revision: Union[str, Sequence[str], None] = 'f6a1d84b2e93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("category", sa.Column("default_team_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_category_default_team_id", "category", "team", ["default_team_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_category_default_team_id", "category", type_="foreignkey")
    op.drop_column("category", "default_team_id")