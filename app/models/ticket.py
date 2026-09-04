"""Modelo de dados para chamados (tickets)."""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import PrioridadeChamado, StatusChamado
from app.models.user import User


class Ticket(SQLModel, table=True):
    """Chamado aberto por um solicitante, podendo ser atendido por um técnico."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: str

    status: StatusChamado = Field(default=StatusChamado.ABERTO, index=True)
    priority: PrioridadeChamado = Field(index=True)

    # Campo temporário como texto livre; será normalizado na Tarefa 2.3
    # (categorias e subcategorias estruturadas).
    category: str = Field(max_length=100)

    requester_id: int = Field(foreign_key="user.id")
    requester: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Ticket.requester_id"}
    )

    assigned_to: int | None = Field(default=None, foreign_key="user.id")
    technician: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Ticket.assigned_to"}
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = Field(default=None)
    closed_at: datetime | None = Field(default=None)