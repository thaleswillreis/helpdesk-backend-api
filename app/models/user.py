"""Modelo de dados para usuários do sistema."""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import NivelAtendimento, pg_enum_column
from app.models.role import Role


class User(SQLModel, table=True):
    """Usuário do sistema (solicitante, técnico ou administrador)."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=120)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_vip: bool = Field(default=False)
    level: NivelAtendimento | None = Field(
        default=None,
        sa_column=pg_enum_column(NivelAtendimento, "nivelatendimento", nullable=True),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    role_id: int | None = Field(default=None, foreign_key="role.id")
    role: Role | None = Relationship()
