"""KPIs de série temporal e desempenho individual por técnico (Tarefa 9.2).

Reaproveita calculate_sla() (Tarefa 4.2); carrega a mesma nota de performance
já documentada em dashboard_service.py (Tarefa 9.1) — agregação em memória,
aceitável no volume atual de um projeto de portfólio.
"""

from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, select

from app.models.enums import NivelAtendimento
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.kpi import KpiTrend, TechnicianKpi, TechnicianKpiList, TrendPoint
from app.services.sla_calculation_service import SLAClockStatus, calculate_sla

_DEFAULT_PERIOD_DAYS = 30
_VALID_GRANULARITIES = {"day", "week", "month"}


def _resolve_period(
    date_from: datetime | None, date_to: datetime | None
) -> tuple[datetime, datetime]:
    resolved_to = date_to or datetime.now(UTC)
    resolved_from = date_from or (resolved_to - timedelta(days=_DEFAULT_PERIOD_DAYS))
    return resolved_from, resolved_to


def _bucket_key(moment: datetime, granularity: str) -> str:
    """Reduz um datetime à chave do bucket (dia/semana/mês) a que ele pertence."""
    d = moment.date()
    if granularity == "day":
        return d.isoformat()
    if granularity == "week":
        monday = d - timedelta(days=d.weekday())
        return monday.isoformat()
    return f"{d.year:04d}-{d.month:02d}"  # month


def _enumerate_buckets(
    date_from: datetime, date_to: datetime, granularity: str
) -> list[str]:
    """Gera todos os buckets do intervalo, mesmo os sem nenhum chamado (evita 'buracos' no gráfico)."""
    buckets: list[str] = []
    seen: set[str] = set()

    cursor = date_from.date()
    end = date_to.date()
    step = {"day": timedelta(days=1), "week": timedelta(weeks=1)}.get(granularity)

    while cursor <= end:
        key = _bucket_key(
            datetime.combine(cursor, datetime.min.time(), tzinfo=UTC), granularity
        )
        if key not in seen:
            buckets.append(key)
            seen.add(key)

        if step is not None:
            cursor += step
        else:  # month
            cursor = date(
                cursor.year + (1 if cursor.month == 12 else 0),
                (cursor.month % 12) + 1,
                1,
            )

    return buckets


def get_kpi_trend(
    session: Session,
    date_from: datetime | None,
    date_to: datetime | None,
    granularity: str,
) -> KpiTrend:
    """Monta a série temporal de volume aberto e cumprimento de SLA por bucket."""
    if granularity not in _VALID_GRANULARITIES:
        granularity = "day"

    resolved_from, resolved_to = _resolve_period(date_from, date_to)

    opened_tickets = list(
        session.exec(
            select(Ticket).where(
                Ticket.created_at >= resolved_from, Ticket.created_at <= resolved_to
            )
        )
    )
    resolved_tickets = list(
        session.exec(
            select(Ticket).where(
                Ticket.resolved_at.is_not(None),
                Ticket.resolved_at >= resolved_from,
                Ticket.resolved_at <= resolved_to,
            )
        )
    )

    opened_counts: dict[str, int] = defaultdict(int)
    for ticket in opened_tickets:
        opened_counts[_bucket_key(ticket.created_at, granularity)] += 1

    resolved_counts: dict[str, int] = defaultdict(int)
    met_counts: dict[str, int] = defaultdict(int)
    breached_counts: dict[str, int] = defaultdict(int)
    for ticket in resolved_tickets:
        key = _bucket_key(ticket.resolved_at, granularity)
        resolved_counts[key] += 1

        sla = calculate_sla(session, ticket)
        if sla is None:
            continue
        if sla["resolution"].status == SLAClockStatus.MET:
            met_counts[key] += 1
        elif sla["resolution"].status == SLAClockStatus.BREACHED:
            breached_counts[key] += 1

    points = []
    for bucket in _enumerate_buckets(resolved_from, resolved_to, granularity):
        met = met_counts[bucket]
        breached = breached_counts[bucket]
        total = met + breached
        compliance = round((met / total) * 100, 1) if total > 0 else None

        points.append(
            TrendPoint(
                bucket=bucket,
                opened_count=opened_counts[bucket],
                resolved_count=resolved_counts[bucket],
                sla_met_count=met,
                sla_breached_count=breached,
                compliance_percentage=compliance,
            )
        )

    return KpiTrend(
        date_from=resolved_from,
        date_to=resolved_to,
        granularity=granularity,
        points=points,
    )


def get_technician_kpis(
    session: Session, date_from: datetime | None, date_to: datetime | None
) -> TechnicianKpiList:
    """Monta os KPIs de desempenho individual de cada técnico com chamado resolvido no período."""
    resolved_from, resolved_to = _resolve_period(date_from, date_to)

    resolved_tickets = list(
        session.exec(
            select(Ticket).where(
                Ticket.resolved_at.is_not(None),
                Ticket.resolved_at >= resolved_from,
                Ticket.resolved_at <= resolved_to,
                Ticket.assigned_to.is_not(None),
            )
        )
    )

    resolution_sums: dict[int, float] = defaultdict(float)
    resolution_counts: dict[int, int] = defaultdict(int)
    met_counts: dict[int, int] = defaultdict(int)
    breached_counts: dict[int, int] = defaultdict(int)
    ticket_counts: dict[int, int] = defaultdict(int)

    for ticket in resolved_tickets:
        technician_id = ticket.assigned_to
        ticket_counts[technician_id] += 1

        sla = calculate_sla(session, ticket)
        if sla is None:
            continue

        resolution = sla["resolution"]
        if resolution.status in (SLAClockStatus.MET, SLAClockStatus.BREACHED):
            resolution_sums[technician_id] += resolution.elapsed_minutes
            resolution_counts[technician_id] += 1
            if resolution.status == SLAClockStatus.MET:
                met_counts[technician_id] += 1
            else:
                breached_counts[technician_id] += 1

    items = []
    for technician_id in sorted(ticket_counts):
        technician = session.get(User, technician_id)
        if technician is None:
            continue

        avg_resolution = (
            round(resolution_sums[technician_id] / resolution_counts[technician_id], 1)
            if resolution_counts[technician_id] > 0
            else None
        )
        met = met_counts[technician_id]
        breached = breached_counts[technician_id]
        total = met + breached
        compliance = round((met / total) * 100, 1) if total > 0 else None

        items.append(
            TechnicianKpi(
                technician_id=technician_id,
                technician_name=technician.name,
                tickets_resolved=ticket_counts[technician_id],
                avg_resolution_minutes=avg_resolution,
                sla_met_count=met,
                sla_breached_count=breached,
                compliance_percentage=compliance,
            )
        )

    return TechnicianKpiList(date_from=resolved_from, date_to=resolved_to, items=items)
