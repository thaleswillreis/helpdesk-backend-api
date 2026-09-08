"""Modelo de dados para categorias de chamados."""

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import PrioridadeChamado
from app.models.team import Team


class Category(SQLModel, table=True):
    """Categoria de classificação de um chamado (ex.: Hardware, Rede, Sistemas)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    default_priority: PrioridadeChamado = Field(
        description="Prioridade sugerida ao abrir um chamado nesta categoria."
    )
    default_team_id: int | None = Field(
        default=None,
        foreign_key="team.id",
        description="Equipe que recebe automaticamente os chamados desta categoria.",
    )
    default_team: Team | None = Relationship()