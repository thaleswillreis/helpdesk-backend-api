"""Modelo de dados para o log de tentativas de entrega de webhook."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class WebhookDelivery(SQLModel, table=True):
    """Registro de uma tentativa de entrega de notificação via webhook."""

    id: int | None = Field(default=None, primary_key=True)
    subscription_id: int = Field(foreign_key="webhooksubscription.id", index=True)
    event_type: str = Field(max_length=100)
    ticket_id: int | None = Field(default=None, foreign_key="ticket.id")
    success: bool
    status_code: int | None = Field(default=None)
    error_message: str | None = Field(default=None)
    attempted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
