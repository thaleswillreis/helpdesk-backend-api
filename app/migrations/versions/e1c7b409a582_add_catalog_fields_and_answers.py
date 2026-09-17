"""add catalog_item_field, ticket.catalog_item_id, ticket_catalog_answer

Revision ID: e1c7b409a582
Revises: d8a4f1c7b350
Create Date: 2026-09-18 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'e1c7b409a582'
down_revision: Union[str, Sequence[str], None] = 'd8a4f1c7b350'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

field_type_enum = postgresql.ENUM("text", "number", "select", name="catalogfieldtype")


def upgrade() -> None:
    """Upgrade schema."""
    field_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "catalogitemfield",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalog_item_id", sa.Integer(), nullable=False),
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
        sa.Column(
            "field_type",
            postgresql.ENUM("text", "number", "select", name="catalogfieldtype", create_type=False),
            nullable=False,
        ),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("options", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["servicecatalogitem.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_catalogitemfield_catalog_item_id"), "catalogitemfield", ["catalog_item_id"], unique=False
    )

    op.add_column("ticket", sa.Column("catalog_item_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ticket_catalog_item_id", "ticket", "servicecatalogitem", ["catalog_item_id"], ["id"]
    )

    op.create_table(
        "ticketcataloganswer",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("field_id", sa.Integer(), nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"]),
        sa.ForeignKeyConstraint(["field_id"], ["catalogitemfield.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ticketcataloganswer_ticket_id"), "ticketcataloganswer", ["ticket_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ticketcataloganswer_ticket_id"), table_name="ticketcataloganswer")
    op.drop_table("ticketcataloganswer")

    op.drop_constraint("fk_ticket_catalog_item_id", "ticket", type_="foreignkey")
    op.drop_column("ticket", "catalog_item_id")

    op.drop_index(op.f("ix_catalogitemfield_catalog_item_id"), table_name="catalogitemfield")
    op.drop_table("catalogitemfield")

    field_type_enum.drop(op.get_bind(), checkfirst=True)