"""add service_catalog_item table

Revision ID: d8a4f1c7b350
Revises: c5e9f2a8d647
Create Date: 2026-09-17 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = 'd8a4f1c7b350'
down_revision: Union[str, Sequence[str], None] = 'c5e9f2a8d647'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "servicecatalogitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("subcategory_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["subcategory_id"], ["subcategory.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("servicecatalogitem")