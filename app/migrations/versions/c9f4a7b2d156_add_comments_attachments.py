"""add ticketcomment, commentmention, and ticketattachment tables

Revision ID: c9f4a7b2d156
Revises: b7d3f9a2c5e8
Create Date: 2026-09-10 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = 'c9f4a7b2d156'
down_revision: Union[str, Sequence[str], None] = 'b7d3f9a2c5e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ticketcomment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticketcomment_ticket_id"), "ticketcomment", ["ticket_id"], unique=False)

    op.create_table(
        "commentmention",
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("mentioned_user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["ticketcomment.id"]),
        sa.ForeignKeyConstraint(["mentioned_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("comment_id", "mentioned_user_id"),
    )

    op.create_table(
        "ticketattachment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("original_filename", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("storage_key", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticketattachment_ticket_id"), "ticketattachment", ["ticket_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ticketattachment_ticket_id"), table_name="ticketattachment")
    op.drop_table("ticketattachment")
    op.drop_table("commentmention")
    op.drop_index(op.f("ix_ticketcomment_ticket_id"), table_name="ticketcomment")
    op.drop_table("ticketcomment")