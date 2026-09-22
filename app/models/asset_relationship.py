"""Modelo de dados para relacionamentos de dependência entre dois ativos."""

from sqlmodel import Field, SQLModel

from app.models.enums import AssetRelationshipType


class AssetRelationship(SQLModel, table=True):
    """Relação de dependência direcionada entre dois ativos (from -> to)."""

    id: int | None = Field(default=None, primary_key=True)
    from_asset_id: int = Field(foreign_key="asset.id", index=True)
    to_asset_id: int = Field(foreign_key="asset.id", index=True)
    relationship_type: AssetRelationshipType
