"""Modelo de dados para equipes de atendimento."""

from sqlmodel import Field, SQLModel


class Team(SQLModel, table=True):
    """Equipe de técnicos responsável por atender chamados de determinado escopo."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: str | None = Field(default=None, max_length=255)