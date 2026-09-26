"""Endpoints de exportação de dados em CSV (Tarefa 9.3). Síncronos.

Exportação assíncrona (via Celery, para relatórios muito grandes, com
download disponibilizado depois) fica registrada como melhoria futura —
fora do escopo desta tarefa.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.models.enums import NivelAtendimento, StatusChamado
from app.services.export_service import (
    export_dashboard_csv,
    export_kpi_trend_csv,
    export_technician_kpis_csv,
    export_tickets_csv,
)

router = APIRouter(prefix="/exports", tags=["dashboard"])


def _csv_response(content: str, filename: str) -> StreamingResponse:
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/tickets.csv")
def export_tickets(
    status_filter: list[StatusChamado] | None = Query(default=None, alias="status"),
    team_id: int | None = None,
    current_level: NivelAtendimento | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sla_status: str | None = None,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> StreamingResponse:
    """Exporta a lista de chamados filtrada em CSV. Restrito a admin/tecnico."""
    content = export_tickets_csv(
        session,
        status_filter,
        team_id,
        current_level,
        created_from,
        created_to,
        sla_status,
    )
    return _csv_response(content, "tickets.csv")


@router.get("/dashboard.csv")
def export_dashboard(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> StreamingResponse:
    """Exporta o dashboard agregado em CSV. Restrito a admin/tecnico."""
    content = export_dashboard_csv(session, date_from, date_to)
    return _csv_response(content, "dashboard.csv")


@router.get("/kpi-trend.csv")
def export_kpi_trend(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    granularity: str = "day",
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> StreamingResponse:
    """Exporta a série temporal de KPIs em CSV. Restrito a admin/tecnico."""
    content = export_kpi_trend_csv(session, date_from, date_to, granularity)
    return _csv_response(content, "kpi_trend.csv")


@router.get("/kpi-technicians.csv")
def export_technician_kpis(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> StreamingResponse:
    """Exporta os KPIs por técnico em CSV. Restrito a admin/tecnico."""
    content = export_technician_kpis_csv(session, date_from, date_to)
    return _csv_response(content, "kpi_technicians.csv")
