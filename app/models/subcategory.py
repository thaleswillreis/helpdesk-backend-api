"""Modelo de dados para subcategorias, vinculadas a uma categoria."""

from sqlmodel import Field, Relationship, SQLModel

from app.models.category import Category


class Subcategory(SQLModel, table=True):
    """Subcategoria de classificação, sempre pertencente a uma categoria."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    category_id: int = Field(foreign_key="category.id")
    category: Category = Relationship()