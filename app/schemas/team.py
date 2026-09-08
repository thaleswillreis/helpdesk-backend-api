"""Contratos de entrada/saída para equipes e seus membros."""

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    """Dados para criar uma equipe."""

    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)


class TeamUpdate(BaseModel):
    """Campos que podem ser atualizados em uma equipe."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class TeamRead(BaseModel):
    """Dados públicos de uma equipe."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None


class TeamMemberAdd(BaseModel):
    """Dados para adicionar um técnico a uma equipe."""

    user_id: int


class TeamMemberRead(BaseModel):
    """Dados públicos de um membro de equipe."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str