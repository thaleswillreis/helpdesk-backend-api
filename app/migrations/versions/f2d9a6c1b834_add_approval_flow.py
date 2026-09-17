"""add service_catalog_item.requires_approval and statuschamado.aguardando_aprovacao

Revision ID: f2d9a6c1b834
Revises: e1c7b409a582
Create Date: 2026-09-19 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'f2d9a6c1b834'
down_revision: Union[str, Sequence[str], None] = 'e1c7b409a582'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "servicecatalogitem",
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Adicionar valor a um enum do Postgres é permitido dentro de transação
    # desde o PG12, desde que o novo valor não seja usado na mesma transação
    # (não é o caso aqui).
    op.execute("ALTER TYPE statuschamado ADD VALUE IF NOT EXISTS 'aguardando_aprovacao'")


def downgrade() -> None:
    """Downgrade schema.

    Nota: o Postgres não oferece um comando direto para remover um valor de
    enum (exigiria recriar o tipo do zero e migrar todas as colunas que o
    usam). Como isso é desproporcional para um downgrade, o valor do enum
    permanece após o rollback — só a coluna nova é revertida.
    """
    op.drop_column("servicecatalogitem", "requires_approval")