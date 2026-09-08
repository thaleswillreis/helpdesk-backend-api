"""Contratos de entrada/saída para categorias e subcategorias."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PrioridadeChamado


class CategoryCreate(BaseModel):
    """Dados para criar uma categoria."""

    name: str = Field(max_length=100)
    default_priority: PrioridadeChamado
    default_team_id: int | None = Field(
        default=None, description="Equipe responsável padrão por esta categoria."
    )


class CategoryUpdate(BaseModel):
    """Campos que podem ser atualizados em uma categoria."""

    name: str | None = Field(default=None, max_length=100)
    default_priority: PrioridadeChamado | None = None
    default_team_id: int | None = None


class CategoryRead(BaseModel):
    """Dados públicos de uma categoria."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    default_priority: PrioridadeChamado
    default_team_id: int | None


class SubcategoryCreate(BaseModel):
    """Dados para criar uma subcategoria."""

    name: str = Field(max_length=100)
    category_id: int


class SubcategoryUpdate(BaseModel):
    """Campos que podem ser atualizados em uma subcategoria."""

    name: str | None = Field(default=None, max_length=100)
    category_id: int | None = None


class SubcategoryRead(BaseModel):
    """Dados públicos de uma subcategoria."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category_id: int