"""Contratos de saída para o histórico de alterações de um chamado."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketHistoryRead(BaseModel):
    """Um evento de alteração registrado no histórico do chamado."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    field_name: str
    old_value: str | None
    new_value: str | None
    comment: str | None
    changed_by: int
    changed_at: datetime