"""Contratos de saída para o dashboard de indicadores (Tarefa 9.1)."""

from datetime import datetime

from pydantic import BaseModel


class CountItem(BaseModel):
    """Uma contagem simples por valor de dimensão (ex: status='aberto', count=12)."""

    dimension_value: str
    count: int


class SlaComplianceItem(BaseModel):
    """Cumprimento de SLA agregado por valor de dimensão (ex: prioridade ou equipe)."""

    dimension_value: str
    met_count: int
    breached_count: int
    compliance_percentage: float


class AverageTimeItem(BaseModel):
    """Tempo médio de atendimento agregado por valor de dimensão."""

    dimension_value: str
    avg_response_minutes: float | None
    avg_resolution_minutes: float | None
    sample_size: int


class DashboardOverview(BaseModel):
    """Indicadores agregados de chamados dentro de um período."""

    date_from: datetime
    date_to: datetime
    total_tickets: int

    volume_by_status: list[CountItem]
    volume_by_team: list[CountItem]
    volume_by_level: list[CountItem]

    sla_compliance_by_priority: list[SlaComplianceItem]
    sla_compliance_by_team: list[SlaComplianceItem]

    average_time_by_team: list[AverageTimeItem]
    average_time_by_category: list[AverageTimeItem]
