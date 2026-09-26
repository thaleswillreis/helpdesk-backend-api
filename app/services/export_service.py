"""Geração de arquivos CSV para exportação de chamados e indicadores (Tarefa 9.3)."""

import csv
import io
from datetime import datetime

from sqlmodel import Session

from app.models.enums import NivelAtendimento, StatusChamado
from app.schemas.ticket import TicketRead
from app.services.dashboard_service import get_dashboard_overview
from app.services.kpi_service import get_kpi_trend, get_technician_kpis
from app.services.sla_calculation_service import calculate_sla
from app.services.ticket_overview_service import get_tickets_overview


def _to_csv(rows: list[dict], fieldnames: list[str]) -> str:
    """Serializa uma lista de dicionários em texto CSV, com cabeçalho."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def export_tickets_csv(
    session: Session,
    status_filter: list[StatusChamado] | None,
    team_id: int | None,
    current_level: NivelAtendimento | None,
    created_from: datetime | None,
    created_to: datetime | None,
    sla_status: str | None,
) -> str:
    """Exporta a lista de chamados filtrada (mesmos filtros do /tickets/overview)."""
    _, results = get_tickets_overview(
        session,
        status_filter=status_filter,
        team_id=team_id,
        current_level=current_level,
        created_from=created_from,
        created_to=created_to,
        sla_status=sla_status,
        skip=0,
        limit=10_000,  # exportação síncrona: teto de segurança, não paginação real
    )

    rows = []
    for ticket, sla in results:
        ticket_data = TicketRead.model_validate(ticket)
        rows.append(
            {
                "id": ticket_data.id,
                "title": ticket_data.title,
                "status": ticket_data.status.value,
                "priority": ticket_data.priority.value,
                "category_id": ticket_data.category_id,
                "team_id": ticket_data.team_id,
                "current_level": ticket_data.current_level.value,
                "requester_id": ticket_data.requester_id,
                "assigned_to": ticket_data.assigned_to,
                "created_at": ticket_data.created_at.isoformat(),
                "resolved_at": ticket_data.resolved_at.isoformat()
                if ticket_data.resolved_at
                else "",
                "closed_at": ticket_data.closed_at.isoformat()
                if ticket_data.closed_at
                else "",
                "sla_response_status": sla["response"].status.value if sla else "",
                "sla_resolution_status": sla["resolution"].status.value if sla else "",
            }
        )

    fieldnames = [
        "id",
        "title",
        "status",
        "priority",
        "category_id",
        "team_id",
        "current_level",
        "requester_id",
        "assigned_to",
        "created_at",
        "resolved_at",
        "closed_at",
        "sla_response_status",
        "sla_resolution_status",
    ]
    return _to_csv(rows, fieldnames)


def export_dashboard_csv(
    session: Session, date_from: datetime | None, date_to: datetime | None
) -> str:
    """Exporta o dashboard agregado (Tarefa 9.1), achatado em linhas de CSV."""
    overview = get_dashboard_overview(session, date_from, date_to)

    rows = []
    for item in overview.volume_by_status:
        rows.append(
            {
                "section": "volume_by_status",
                "dimension": item.dimension_value,
                "metric": "count",
                "value": item.count,
            }
        )
    for item in overview.volume_by_team:
        rows.append(
            {
                "section": "volume_by_team",
                "dimension": item.dimension_value,
                "metric": "count",
                "value": item.count,
            }
        )
    for item in overview.volume_by_level:
        rows.append(
            {
                "section": "volume_by_level",
                "dimension": item.dimension_value,
                "metric": "count",
                "value": item.count,
            }
        )
    for item in overview.sla_compliance_by_priority:
        rows.append(
            {
                "section": "sla_compliance_by_priority",
                "dimension": item.dimension_value,
                "metric": "compliance_percentage",
                "value": item.compliance_percentage,
            }
        )
    for item in overview.sla_compliance_by_team:
        rows.append(
            {
                "section": "sla_compliance_by_team",
                "dimension": item.dimension_value,
                "metric": "compliance_percentage",
                "value": item.compliance_percentage,
            }
        )
    for item in overview.average_time_by_team:
        rows.append(
            {
                "section": "average_time_by_team",
                "dimension": item.dimension_value,
                "metric": "avg_resolution_minutes",
                "value": item.avg_resolution_minutes,
            }
        )
    for item in overview.average_time_by_category:
        rows.append(
            {
                "section": "average_time_by_category",
                "dimension": item.dimension_value,
                "metric": "avg_resolution_minutes",
                "value": item.avg_resolution_minutes,
            }
        )

    return _to_csv(rows, ["section", "dimension", "metric", "value"])


def export_kpi_trend_csv(
    session: Session,
    date_from: datetime | None,
    date_to: datetime | None,
    granularity: str,
) -> str:
    """Exporta a série temporal de KPIs (Tarefa 9.2)."""
    trend = get_kpi_trend(session, date_from, date_to, granularity)

    rows = [
        {
            "bucket": point.bucket,
            "opened_count": point.opened_count,
            "resolved_count": point.resolved_count,
            "sla_met_count": point.sla_met_count,
            "sla_breached_count": point.sla_breached_count,
            "compliance_percentage": point.compliance_percentage,
        }
        for point in trend.points
    ]
    fieldnames = [
        "bucket",
        "opened_count",
        "resolved_count",
        "sla_met_count",
        "sla_breached_count",
        "compliance_percentage",
    ]
    return _to_csv(rows, fieldnames)


def export_technician_kpis_csv(
    session: Session, date_from: datetime | None, date_to: datetime | None
) -> str:
    """Exporta os KPIs de desempenho por técnico (Tarefa 9.2)."""
    kpis = get_technician_kpis(session, date_from, date_to)

    rows = [
        {
            "technician_id": item.technician_id,
            "technician_name": item.technician_name,
            "tickets_resolved": item.tickets_resolved,
            "avg_resolution_minutes": item.avg_resolution_minutes,
            "sla_met_count": item.sla_met_count,
            "sla_breached_count": item.sla_breached_count,
            "compliance_percentage": item.compliance_percentage,
        }
        for item in kpis.items
    ]
    fieldnames = [
        "technician_id",
        "technician_name",
        "tickets_resolved",
        "avg_resolution_minutes",
        "sla_met_count",
        "sla_breached_count",
        "compliance_percentage",
    ]
    return _to_csv(rows, fieldnames)
