"""Modelo de dados para campos configuráveis de um item do catálogo de serviços."""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel

from app.models.enums import CatalogFieldType


class CatalogItemField(SQLModel, table=True):
    """Campo de formulário configurável, pertencente a um item do catálogo."""

    id: int | None = Field(default=None, primary_key=True)
    catalog_item_id: int = Field(foreign_key="servicecatalogitem.id", index=True)

    label: str = Field(max_length=150)
    field_type: CatalogFieldType
    is_required: bool = Field(default=True)
    options: list[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    display_order: int = Field(default=0)