"""Modelo de dados para o histórico de alterações de um chamado."""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User


class TicketHistory(SQLModel, table=True):
    """Registro de uma única alteração de campo em um chamado."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)

    field_name: str = Field(max_length=50)
    old_value: str | None = Field(default=None)
    new_value: str | None = Field(default=None)
    comment: str | None = Field(default=None)

    changed_by: int = Field(foreign_key="user.id")
    user: User = Relationship()

    changed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))