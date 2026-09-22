"""add asset and asset_relationship tables

Revision ID: e5b8f2d4a731
Revises: d3f7a1c9e628
Create Date: 2026-09-24 09:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e5b8f2d4a731"
down_revision: Union[str, Sequence[str], None] = "d3f7a1c9e628"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

asset_type_enum = postgresql.ENUM(
    "notebook",
    "desktop",
    "monitor",
    "impressora",
    "servidor",
    "servidor_virtual",
    "switch",
    "roteador",
    "nobreak",
    "outro",
    name="assettype",
)
asset_status_enum = postgresql.ENUM(
    "em_uso", "estoque", "manutencao", "baixado", name="assetstatus"
)
relationship_type_enum = postgresql.ENUM(
    "hospeda", "conectado_a", "alimenta", "mesma_rede_que", name="assetrelationshiptype"
)


def upgrade() -> None:
    """Upgrade schema."""
    asset_type_enum.create(op.get_bind(), checkfirst=True)
    asset_status_enum.create(op.get_bind(), checkfirst=True)
    relationship_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "asset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
        sa.Column(
            "asset_type",
            postgresql.ENUM(
                "notebook",
                "desktop",
                "monitor",
                "impressora",
                "servidor",
                "servidor_virtual",
                "switch",
                "roteador",
                "nobreak",
                "outro",
                name="assettype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "serial_number", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "em_uso",
                "estoque",
                "manutencao",
                "baixado",
                name="assetstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "location", sqlmodel.sql.sqltypes.AutoString(length=150), nullable=True
        ),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_to"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
    )

    op.create_table(
        "assetrelationship",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_asset_id", sa.Integer(), nullable=False),
        sa.Column("to_asset_id", sa.Integer(), nullable=False),
        sa.Column(
            "relationship_type",
            postgresql.ENUM(
                "hospeda",
                "conectado_a",
                "alimenta",
                "mesma_rede_que",
                name="assetrelationshiptype",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["from_asset_id"], ["asset.id"]),
        sa.ForeignKeyConstraint(["to_asset_id"], ["asset.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assetrelationship_from_asset_id"),
        "assetrelationship",
        ["from_asset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assetrelationship_to_asset_id"),
        "assetrelationship",
        ["to_asset_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_assetrelationship_to_asset_id"), table_name="assetrelationship"
    )
    op.drop_index(
        op.f("ix_assetrelationship_from_asset_id"), table_name="assetrelationship"
    )
    op.drop_table("assetrelationship")
    op.drop_table("asset")

    relationship_type_enum.drop(op.get_bind(), checkfirst=True)
    asset_status_enum.drop(op.get_bind(), checkfirst=True)
    asset_type_enum.drop(op.get_bind(), checkfirst=True)
