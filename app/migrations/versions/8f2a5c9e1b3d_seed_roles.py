"""seed initial roles

Revision ID: 8f2a5c9e1b3d
Revises: 1ac767e8c07e
Create Date: 2026-09-03 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '8f2a5c9e1b3d'
down_revision: Union[str, Sequence[str], None] = '1ac767e8c07e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_table = sa.table(
    "role",
    sa.column("name", sa.String),
    sa.column("description", sa.String),
)

ROLES = [
    {"name": "admin", "description": "Administrador do sistema, acesso total."},
    {"name": "tecnico", "description": "Atende e resolve chamados."},
    {"name": "solicitante", "description": "Abre chamados e acompanha o próprio atendimento."},
]


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(role_table, ROLES)


def downgrade() -> None:
    """Downgrade schema."""
    names = tuple(role["name"] for role in ROLES)
    op.execute(role_table.delete().where(role_table.c.name.in_(names)))