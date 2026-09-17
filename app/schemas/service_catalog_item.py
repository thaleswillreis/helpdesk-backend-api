"""Contratos de entrada/saída para itens do catálogo de serviços."""

from pydantic import BaseModel, ConfigDict, Field


class ServiceCatalogItemCreate(BaseModel):
    """Dados para criar um item do catálogo."""

    name: str = Field(max_length=150)
    description: str = Field(min_length=1)
    category_id: int
    subcategory_id: int | None = None
    requires_approval: bool = False


class ServiceCatalogItemUpdate(BaseModel):
    """Campos que podem ser atualizados em um item do catálogo."""

    name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, min_length=1)
    category_id: int | None = None
    subcategory_id: int | None = None
    is_active: bool | None = None
    requires_approval: bool | None = None


class ServiceCatalogItemRead(BaseModel):
    """Dados públicos de um item do catálogo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category_id: int
    subcategory_id: int | None
    is_active: bool
    requires_approval: bool