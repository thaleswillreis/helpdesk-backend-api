"""Modelo de dados para chamados (tickets)."""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.category import Category
from app.models.enums import NivelAtendimento, PrioridadeChamado, StatusChamado
from app.models.subcategory import Subcategory
from app.models.team import Team
from app.models.user import User


class Ticket(SQLModel, table=True):
    """Chamado aberto por um solicitante, podendo ser atendido por um técnico."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    description: str

    status: StatusChamado = Field(default=StatusChamado.ABERTO, index=True)
    priority: PrioridadeChamado = Field(index=True)

    category_id: int = Field(foreign_key="category.id")
    category: Category = Relationship()

    subcategory_id: int | None = Field(default=None, foreign_key="subcategory.id")
    subcategory: Subcategory | None = Relationship()

    requester_id: int = Field(foreign_key="user.id")
    requester: User = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Ticket.requester_id"}
    )

    assigned_to: int | None = Field(default=None, foreign_key="user.id")
    technician: User | None = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Ticket.assigned_to"}
    )

    team_id: int | None = Field(default=None, foreign_key="team.id")
    team: Team | None = Relationship()

    current_level: NivelAtendimento = Field(
        default=NivelAtendimento.N1,
        description="Fila de nível de atendimento em que o chamado está atualmente.",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = Field(default=None)
    closed_at: datetime | None = Field(default=None)