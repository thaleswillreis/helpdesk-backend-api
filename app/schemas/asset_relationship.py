"""Contratos de entrada/saída para relacionamentos entre ativos."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AssetRelationshipType


class AssetRelationshipCreate(BaseModel):
    """Dados para criar um relacionamento de dependência entre dois ativos."""

    from_asset_id: int
    to_asset_id: int
    relationship_type: AssetRelationshipType

    @model_validator(mode="after")
    def _assets_must_differ(self) -> "AssetRelationshipCreate":
        if self.from_asset_id == self.to_asset_id:
            raise ValueError("Um ativo não pode se relacionar consigo mesmo.")
        return self


class AssetRelationshipRead(BaseModel):
    """Dados públicos de um relacionamento entre ativos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    from_asset_id: int
    to_asset_id: int
    relationship_type: AssetRelationshipType
