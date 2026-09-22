"""Modelo de dados para assinaturas de webhook (notificações externas)."""

from datetime import UTC, datetime

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel


class WebhookSubscription(SQLModel, table=True):
    """Assinatura de webhook: URL externa que recebe notificações de eventos do sistema."""

    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(max_length=500)
    secret: str = Field(max_length=255, description="Usado para assinar o payload via HMAC-SHA256.")
    is_active: bool = Field(default=True)
    subscribed_events: list[str] = Field(sa_column=Column(ARRAY(String)))

    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))