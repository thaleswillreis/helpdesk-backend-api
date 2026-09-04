"""create ticket table

Revision ID: b3c72f184a90
Revises: 8f2a5c9e1b3d
Create Date: 2026-09-04 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'b3c72f184a90'
down_revision: Union[str, Sequence[str], None] = '8f2a5c9e1b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: a criação/remoção do tipo é feita manualmente abaixo,
# evitando que o SQLAlchemy tente criar o tipo de novo ao criar a tabela.
status_enum = postgresql.ENUM(
    "aberto",
    "em_atendimento",
    "aguardando_solicitante",
    "resolvido",
    "fechado",
    "cancelado",
    name="statuschamado",
    create_type=False,
)

priority_enum = postgresql.ENUM(
    "baixa",
    "media",
    "alta",
    "critica",
    "vip",
    name="prioridadechamado",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    status_enum.create(op.get_bind(), checkfirst=True)
    priority_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ticket",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", status_enum, nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["requester_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ticket_status"), "ticket", ["status"], unique=False)
    op.create_index(op.f("ix_ticket_priority"), "ticket", ["priority"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_ticket_priority"), table_name="ticket")
    op.drop_index(op.f("ix_ticket_status"), table_name="ticket")
    op.drop_table("ticket")
    priority_enum.drop(op.get_bind(), checkfirst=True)
    status_enum.drop(op.get_bind(), checkfirst=True)