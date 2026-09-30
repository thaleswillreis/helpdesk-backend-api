"""Modelo de dados para ativos cadastrados no CMDB."""

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import AssetStatus, AssetType, pg_enum_column
from app.models.user import User


class Asset(SQLModel, table=True):
    """Um equipamento/ativo de TI cadastrado no CMDB."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=150)
    asset_type: AssetType = Field(sa_column=pg_enum_column(AssetType, "assettype"))
    serial_number: str | None = Field(default=None, max_length=100, unique=True)
    status: AssetStatus = Field(
        default=AssetStatus.EM_USO,
        sa_column=pg_enum_column(AssetStatus, "assetstatus"),
    )
    location: str | None = Field(default=None, max_length=150)

    assigned_to: int | None = Field(default=None, foreign_key="user.id")
    responsible: User | None = Relationship()
