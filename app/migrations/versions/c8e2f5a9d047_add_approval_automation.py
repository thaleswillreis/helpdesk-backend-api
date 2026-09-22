"""add approval automation fields and system user

Revision ID: c8e2f5a9d047
Revises: b6d4f8a1c973
Create Date: 2026-09-22 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c8e2f5a9d047"
down_revision: Union[str, Sequence[str], None] = "b6d4f8a1c973"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

action_enum = postgresql.ENUM(
    "auto_approve", "auto_reject", name="approvaltimeoutaction"
)


def upgrade() -> None:
    """Upgrade schema."""
    action_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "servicecatalogitem",
        sa.Column(
            "auto_approve_if_vip",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "servicecatalogitem",
        sa.Column("approval_timeout_hours", sa.Integer(), nullable=True),
    )
    op.add_column(
        "servicecatalogitem",
        sa.Column(
            "approval_timeout_action",
            postgresql.ENUM(
                "auto_approve",
                "auto_reject",
                name="approvaltimeoutaction",
                create_type=False,
            ),
            nullable=True,
        ),
    )

    # Usuário "sistema": ator técnico para decisões de aprovação automatizadas
    # (VIP e timeout), reaproveitando o mesmo fluxo de auditoria de um admin humano.
    op.execute(
        """
        INSERT INTO "user" (name, email, hashed_password, is_active, is_vip, created_at, role_id)
        SELECT 'Automação do Sistema', 'automation@system.local', 'unusable-system-account', true, false, now(), id
        FROM role WHERE name = 'admin'
        ON CONFLICT (email) DO NOTHING
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM \"user\" WHERE email = 'automation@system.local'")

    op.drop_column("servicecatalogitem", "approval_timeout_action")
    op.drop_column("servicecatalogitem", "approval_timeout_hours")
    op.drop_column("servicecatalogitem", "auto_approve_if_vip")

    action_enum.drop(op.get_bind(), checkfirst=True)
