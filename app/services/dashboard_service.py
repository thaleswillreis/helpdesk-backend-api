"""Agregações de indicadores para o dashboard de gestão (Tarefa 9.1).

Nota de performance (mesma limitação já documentada em ticket_overview_service,
Tarefa 4.3): como o status de SLA é sempre calculado sob demanda (não é uma
coluna armazenada), este módulo roda calculate_sla() para cada chamado do
período e agrega em memória, em vez de uma agregação pura em SQL. Aceitável no
volume de um projeto de portfólio; escalaria melhor materializando o status de
SLA periodicamente (ex: um job do Celery Beat), quando a base crescer.
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.models.category import Category
from app.models.team import Team
from app.models.ticket import Ticket
from app.schemas.dashboard import (
    AverageTimeItem,
    CountItem,
    DashboardOverview,
    SlaComplianceItem,
)
from app.services.sla_calculation_service import SLAClockStatus, calculate_sla

_DEFAULT_PERIOD_DAYS = 30


def _resolve_period(
    date_from: datetime | None, date_to: datetime | None
) -> tuple[datetime, datetime]:
    """Resolve o período padrão (últimos 30 dias) quando não informado explicitamente."""
    resolved_to = date_to or datetime.now(UTC)
    resolved_from = date_from or (resolved_to - timedelta(days=_DEFAULT_PERIOD_DAYS))
    return resolved_from, resolved_to


def _count_by(tickets: list[Ticket], key_fn) -> list[CountItem]:
    counts: dict[str, int] = defaultdict(int)
    for ticket in tickets:
        key = key_fn(ticket)
        if key is not None:
            counts[key] += 1
    return [CountItem(dimension_value=k, count=v) for k, v in sorted(counts.items())]


def _sla_compliance_by(
    session: Session, tickets: list[Ticket], key_fn
) -> list[SlaComplianceItem]:
    """Compõe % de cumprimento de SLA (met vs breached) entre chamados já resolvidos."""
    tallies: dict[str, dict[str, int]] = defaultdict(lambda: {"met": 0, "breached": 0})

    for ticket in tickets:
        if ticket.resolved_at is None:
            continue

        sla = calculate_sla(session, ticket)
        if sla is None:
            continue

        resolution_status = sla["resolution"].status
        if resolution_status not in (SLAClockStatus.MET, SLAClockStatus.BREACHED):
            continue

        key = key_fn(ticket)
        if key is None:
            continue

        tallies[key][
            "met" if resolution_status == SLAClockStatus.MET else "breached"
        ] += 1

    items = []
    for key, counts in sorted(tallies.items()):
        total = counts["met"] + counts["breached"]
        percentage = round((counts["met"] / total) * 100, 1) if total > 0 else 0.0
        items.append(
            SlaComplianceItem(
                dimension_value=key,
                met_count=counts["met"],
                breached_count=counts["breached"],
                compliance_percentage=percentage,
            )
        )
    return items


def _average_time_by(
    session: Session, tickets: list[Ticket], key_fn
) -> list[AverageTimeItem]:
    """Calcula o tempo médio (minutos úteis) até resposta e resolução, por dimensão."""
    response_sums: dict[str, float] = defaultdict(float)
    response_counts: dict[str, int] = defaultdict(int)
    resolution_sums: dict[str, float] = defaultdict(float)
    resolution_counts: dict[str, int] = defaultdict(int)
    sample_sizes: dict[str, int] = defaultdict(int)

    for ticket in tickets:
        key = key_fn(ticket)
        if key is None:
            continue

        sla = calculate_sla(session, ticket)
        if sla is None:
            continue

        sample_sizes[key] += 1

        response = sla["response"]
        if response.status in (SLAClockStatus.MET, SLAClockStatus.BREACHED):
            response_sums[key] += response.elapsed_minutes
            response_counts[key] += 1

        resolution = sla["resolution"]
        if resolution.status in (SLAClockStatus.MET, SLAClockStatus.BREACHED):
            resolution_sums[key] += resolution.elapsed_minutes
            resolution_counts[key] += 1

    items = []
    for key in sorted(sample_sizes):
        avg_response = (
            round(response_sums[key] / response_counts[key], 1)
            if response_counts[key] > 0
            else None
        )
        avg_resolution = (
            round(resolution_sums[key] / resolution_counts[key], 1)
            if resolution_counts[key] > 0
            else None
        )
        items.append(
            AverageTimeItem(
                dimension_value=key,
                avg_response_minutes=avg_response,
                avg_resolution_minutes=avg_resolution,
                sample_size=sample_sizes[key],
            )
        )
    return items


def get_dashboard_overview(
    session: Session, date_from: datetime | None, date_to: datetime | None
) -> DashboardOverview:
    """Monta o dashboard agregado de indicadores para o período informado."""
    resolved_from, resolved_to = _resolve_period(date_from, date_to)

    tickets = list(
        session.exec(
            select(Ticket).where(
                Ticket.created_at >= resolved_from, Ticket.created_at <= resolved_to
            )
        )
    )

    teams_by_id = {t.id: t.name for t in session.exec(select(Team))}
    categories_by_id = {c.id: c.name for c in session.exec(select(Category))}

    return DashboardOverview(
        date_from=resolved_from,
        date_to=resolved_to,
        total_tickets=len(tickets),
        volume_by_status=_count_by(tickets, lambda t: t.status.value),
        volume_by_team=_count_by(
            tickets, lambda t: teams_by_id.get(t.team_id) if t.team_id else "Sem equipe"
        ),
        volume_by_level=_count_by(tickets, lambda t: t.current_level.value),
        sla_compliance_by_priority=_sla_compliance_by(
            session, tickets, lambda t: t.priority.value
        ),
        sla_compliance_by_team=_sla_compliance_by(
            session,
            tickets,
            lambda t: teams_by_id.get(t.team_id) if t.team_id else "Sem equipe",
        ),
        average_time_by_team=_average_time_by(
            session,
            tickets,
            lambda t: teams_by_id.get(t.team_id) if t.team_id else "Sem equipe",
        ),
        average_time_by_category=_average_time_by(
            session,
            tickets,
            lambda t: categories_by_id.get(t.category_id, "Categoria desconhecida"),
        ),
    )
