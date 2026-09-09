"""Contratos de saída para o status de SLA de um chamado."""

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PrioridadeChamado
from app.services.sla_calculation_service import SLAClockStatus


class SLAClockRead(BaseModel):
    """Situação de um relógio de SLA (resposta ou solução)."""

    target_minutes: int
    elapsed_minutes: float
    status: SLAClockStatus
    due_at: datetime | None


class TicketSLARead(BaseModel):
    """Situação completa de SLA de um chamado."""

    applicable: bool
    priority: PrioridadeChamado | None = None
    response: SLAClockRead | None = None
    resolution: SLAClockRead | None = None