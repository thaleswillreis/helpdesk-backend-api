"""Endpoints de KPIs: série temporal e desempenho por técnico (Tarefa 9.2)."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.kpi import KpiTrend, TechnicianKpiList
from app.services.kpi_service import get_kpi_trend, get_technician_kpis

router = APIRouter(prefix="/kpis", tags=["dashboard"])


@router.get("/trend", response_model=KpiTrend)
def read_kpi_trend(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    granularity: str = "day",
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> KpiTrend:
    """Série temporal de volume e cumprimento de SLA (granularity: day/week/month).

    Se date_from/date_to forem omitidos, usa os últimos 30 dias. Restrito a admin/tecnico.
    """
    return get_kpi_trend(session, date_from, date_to, granularity)


@router.get("/technicians", response_model=TechnicianKpiList)
def read_technician_kpis(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> TechnicianKpiList:
    """Desempenho individual de cada técnico com chamado resolvido no período.

    Se date_from/date_to forem omitidos, usa os últimos 30 dias. Restrito a admin/tecnico.
    """
    return get_technician_kpis(session, date_from, date_to)
