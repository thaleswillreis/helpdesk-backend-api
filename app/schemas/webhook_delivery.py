"""Contratos de saída para o log de entregas de webhook."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WebhookDeliveryRead(BaseModel):
    """Registro público de uma tentativa de entrega de webhook."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    event_type: str
    ticket_id: int | None
    success: bool
    status_code: int | None
    error_message: str | None
    attempted_at: datetime
