"""Modelo de dados para itens do catálogo de serviços."""

from sqlmodel import Field, Relationship, SQLModel

from app.models.category import Category
from app.models.subcategory import Subcategory


class ServiceCatalogItem(SQLModel, table=True):
    """Item padronizado do catálogo de serviços, vinculado a uma categoria de chamado."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=150)
    description: str

    category_id: int = Field(foreign_key="category.id")
    category: Category = Relationship()

    subcategory_id: int | None = Field(default=None, foreign_key="subcategory.id")
    subcategory: Subcategory | None = Relationship()

    is_active: bool = Field(default=True)
    requires_approval: bool = Field(
        default=False,
        description="Se True, chamados abertos a partir deste item nascem aguardando aprovação.",
    )