"""Modelo de dados para papéis (roles) de usuário."""

from sqlmodel import Field, SQLModel


class Role(SQLModel, table=True):
    """Papel atribuído a um usuário (ex.: admin, técnico, solicitante)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=50)
    description: str | None = Field(default=None, max_length=255)