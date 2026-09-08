"""Contratos de entrada/saída para usuários."""

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import NivelAtendimento


class UserCreate(BaseModel):
    """Dados necessários para criar um novo usuário."""

    name: str = Field(max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role_name: str = Field(description="Nome do papel: admin, tecnico ou solicitante")
    level: NivelAtendimento | None = Field(
        default=None, description="Nível de atendimento (N1/N2/N3), relevante só para técnicos."
    )


class UserRead(BaseModel):
    """Dados públicos de um usuário, retornados pela API."""

    id: int
    name: str
    email: str
    role_name: str | None
    is_active: bool
    level: NivelAtendimento | None = None