"""Contratos de entrada/saída para assinaturas de webhook."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import WebhookEventType


class WebhookSubscriptionCreate(BaseModel):
    """Dados para criar uma assinatura de webhook."""

    url: str = Field(max_length=500)
    secret: str = Field(min_length=8, max_length=255)
    subscribed_events: list[WebhookEventType] = Field(min_length=1)


class WebhookSubscriptionUpdate(BaseModel):
    """Campos que podem ser atualizados em uma assinatura de webhook."""

    url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    subscribed_events: list[WebhookEventType] | None = None


class WebhookSubscriptionRead(BaseModel):
    """Dados públicos de uma assinatura de webhook. O segredo NUNCA é retornado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    is_active: bool
    subscribed_events: list[str]
    created_by: int
    created_at: datetime
