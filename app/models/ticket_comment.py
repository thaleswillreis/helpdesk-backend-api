"""Modelo de dados para comentários (internos ou públicos) de um chamado."""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User


class TicketComment(SQLModel, table=True):
    """Comentário associado a um chamado, podendo ser interno (só staff) ou público."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)

    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship()

    content: str
    is_internal: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))