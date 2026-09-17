"""add ticket_article table

Revision ID: c5e9f2a8d647
Revises: b3f8a45c9e2c
Create Date: 2026-09-16 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c5e9f2a8d647'
down_revision: Union[str, Sequence[str], None] = 'b3f8a45c9e2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ticketarticle",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("is_resolution", sa.Boolean(), nullable=False),
        sa.Column("linked_by", sa.Integer(), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.ForeignKeyConstraint(["article_id"], ["article.id"]),
        sa.ForeignKeyConstraint(["linked_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticketarticle_ticket_id"), "ticketarticle", ["ticket_id"], unique=False)
    op.create_index(op.f("ix_ticketarticle_article_id"), "ticketarticle", ["article_id"], unique=False)
    op.create_unique_constraint(
        "uq_ticketarticle_ticket_article", "ticketarticle", ["ticket_id", "article_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_ticketarticle_ticket_article", "ticketarticle", type_="unique")
    op.drop_index(op.f("ix_ticketarticle_article_id"), table_name="ticketarticle")
    op.drop_index(op.f("ix_ticketarticle_ticket_id"), table_name="ticketarticle")
    op.drop_table("ticketarticle")