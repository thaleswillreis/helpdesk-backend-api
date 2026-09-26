"""Contratos de saída para KPIs: série temporal e desempenho por técnico (Tarefa 9.2)."""

from datetime import datetime

from pydantic import BaseModel


class TrendPoint(BaseModel):
    """Um ponto da série temporal (um bucket de tempo: dia, semana ou mês)."""

    bucket: str
    opened_count: int
    resolved_count: int
    sla_met_count: int
    sla_breached_count: int
    compliance_percentage: float | None


class KpiTrend(BaseModel):
    """Série temporal de volume e cumprimento de SLA."""

    date_from: datetime
    date_to: datetime
    granularity: str
    points: list[TrendPoint]


class TechnicianKpi(BaseModel):
    """Indicadores de desempenho de um técnico individual no período."""

    technician_id: int
    technician_name: str
    tickets_resolved: int
    avg_resolution_minutes: float | None
    sla_met_count: int
    sla_breached_count: int
    compliance_percentage: float | None


class TechnicianKpiList(BaseModel):
    """Lista de KPIs por técnico no período."""

    date_from: datetime
    date_to: datetime
    items: list[TechnicianKpi]
