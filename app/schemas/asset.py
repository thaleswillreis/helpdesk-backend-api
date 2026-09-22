"""Contratos de entrada/saída para ativos do CMDB."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssetStatus, AssetType


class AssetCreate(BaseModel):
    """Dados para cadastrar um ativo."""

    name: str = Field(max_length=150)
    asset_type: AssetType
    serial_number: str | None = Field(default=None, max_length=100)
    status: AssetStatus = AssetStatus.EM_USO
    location: str | None = Field(default=None, max_length=150)
    assigned_to: int | None = None


class AssetUpdate(BaseModel):
    """Campos que podem ser atualizados em um ativo existente."""

    name: str | None = Field(default=None, max_length=150)
    asset_type: AssetType | None = None
    serial_number: str | None = Field(default=None, max_length=100)
    status: AssetStatus | None = None
    location: str | None = Field(default=None, max_length=150)
    assigned_to: int | None = None


class AssetRead(BaseModel):
    """Dados públicos de um ativo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    asset_type: AssetType
    serial_number: str | None
    status: AssetStatus
    location: str | None
    assigned_to: int | None
