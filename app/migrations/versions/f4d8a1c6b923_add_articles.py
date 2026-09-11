"""add article table

Revision ID: f4d8a1c6b923
Revises: e2b6c9a4f731
Create Date: 2026-09-13 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'f4d8a1c6b923'
down_revision: Union[str, Sequence[str], None] = 'e2b6c9a4f731'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

article_status_enum = postgresql.ENUM("draft", "published", name="articlestatus")


def upgrade() -> None:
    """Upgrade schema."""
    article_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "article",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("draft", "published", name="articlestatus", create_type=False),
            nullable=False,
        ),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("subcategory_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["subcategory_id"], ["subcategory.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_article_status"), "article", ["status"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_article_status"), table_name="article")
    op.drop_table("article")
    article_status_enum.drop(op.get_bind(), checkfirst=True)