"""add category, subcategory, user.is_vip, and ticket category FKs

Revision ID: d47e1a92c8b1
Revises: b3c72f184a90
Create Date: 2026-09-05 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'd47e1a92c8b1'
down_revision: Union[str, Sequence[str], None] = 'b3c72f184a90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# O tipo 'prioridadechamado' já existe (criado na migration do Ticket).
# create_type=False: aqui só referenciamos o tipo existente, sem recriá-lo.
priority_enum = postgresql.ENUM(
    "baixa", "media", "alta", "critica", "vip",
    name="prioridadechamado",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user",
        sa.Column("is_vip", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "category",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("default_priority", priority_enum, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_category_name"), "category", ["name"], unique=True)

    op.create_table(
        "subcategory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.drop_column("ticket", "category")
    op.add_column("ticket", sa.Column("category_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_ticket_category_id", "ticket", "category", ["category_id"], ["id"]
    )
    op.add_column("ticket", sa.Column("subcategory_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ticket_subcategory_id", "ticket", "subcategory", ["subcategory_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_ticket_subcategory_id", "ticket", type_="foreignkey")
    op.drop_column("ticket", "subcategory_id")
    op.drop_constraint("fk_ticket_category_id", "ticket", type_="foreignkey")
    op.drop_column("ticket", "category_id")
    op.add_column(
        "ticket",
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    )

    op.drop_table("subcategory")
    op.drop_index(op.f("ix_category_name"), table_name="category")
    op.drop_table("category")

    op.drop_column("user", "is_vip")