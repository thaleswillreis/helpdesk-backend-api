"""Contratos de entrada/saída para campos de formulário de itens do catálogo."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CatalogFieldType


class CatalogItemFieldCreate(BaseModel):
    """Dados para criar um campo de formulário em um item do catálogo."""

    label: str = Field(max_length=150)
    field_type: CatalogFieldType
    is_required: bool = True
    options: list[str] | None = Field(
        default=None, description="Obrigatório e usado somente quando field_type='select'."
    )
    display_order: int = 0


class CatalogItemFieldUpdate(BaseModel):
    """Campos que podem ser atualizados em um campo de formulário existente."""

    label: str | None = Field(default=None, max_length=150)
    field_type: CatalogFieldType | None = None
    is_required: bool | None = None
    options: list[str] | None = None
    display_order: int | None = None


class CatalogItemFieldRead(BaseModel):
    """Dados públicos de um campo de formulário."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_item_id: int
    label: str
    field_type: CatalogFieldType
    is_required: bool
    options: list[str] | None
    display_order: int