"""Endpoint do dashboard de indicadores de gestão."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import get_dashboard_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def read_dashboard_overview(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> DashboardOverview:
    """Retorna volume, cumprimento de SLA e tempo médio de atendimento no período.

    Se date_from/date_to forem omitidos, usa os últimos 30 dias por padrão.
    Restrito a admin/tecnico.
    """
    return get_dashboard_overview(session, date_from, date_to)
