"""Modelo de dados para categorias de chamados."""

from sqlmodel import Field, SQLModel

from app.models.enums import PrioridadeChamado


class Category(SQLModel, table=True):
    """Categoria de classificação de um chamado (ex.: Hardware, Rede, Sistemas)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    default_priority: PrioridadeChamado = Field(
        description="Prioridade sugerida ao abrir um chamado nesta categoria."
    )