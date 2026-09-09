"""Cálculo dos indicadores de SLA (resposta e solução) de um chamado."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Session, select

from app.models.enums import StatusChamado
from app.models.sla_policy import SLAPolicy
from app.models.team_schedule import TeamSchedule
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.services.business_time import (
    add_business_minutes, 
    business_minutes_between, 
    expand_schedule)
from app.services.system_settings_service import get_settings


def _ensure_utc(dt: datetime) -> datetime:
    """Normaliza um datetime lido do banco (naive) para UTC-aware.

    A coluna do Postgres não guarda fuso horário, então valores vindos do
    banco retornam sem tzinfo — mas sempre representam UTC (é assim que
    gravamos em toda a aplicação). Isso evita TypeError ao comparar com
    datetimes 'aware' gerados em memória (ex.: datetime.now(UTC)).
    """
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

_PAUSING_STATUS_VALUE = StatusChamado.AGUARDANDO_SOLICITANTE.value


class SLAClockStatus(StrEnum):
    """Situação de um relógio de SLA (resposta ou solução)."""

    MET = "met"
    BREACHED = "breached"
    AT_RISK = "at_risk"
    PENDING = "pending"
    PAUSED = "paused"


@dataclass
class SLAClockResult:
    """Resultado do cálculo de um relógio de SLA."""

    target_minutes: int
    elapsed_minutes: float
    status: SLAClockStatus
    due_at: datetime | None


@dataclass
class _Segment:
    start: datetime
    end: datetime | None  # None = segmento aberto (projeção futura)
    team_id: int | None
    is_paused: bool


def _reconstruct_field_timeline(
    ticket: Ticket, history: list[TicketHistory], field_name: str
) -> list[tuple[datetime, str | None]]:
    """Reconstrói a linha do tempo de valores de um campo, do created_at ao valor atual."""
    changes = sorted(
        (h for h in history if h.field_name == field_name), key=lambda h: h.changed_at
    )
    if not changes:
        current = getattr(ticket, field_name)
        return [(_ensure_utc(ticket.created_at), str(current) if current is not None else None)]

    timeline = [(_ensure_utc(ticket.created_at), changes[0].old_value)]
    for change in changes:
        timeline.append((_ensure_utc(change.changed_at), change.new_value))
    return timeline


def _value_at(timeline: list[tuple[datetime, str | None]], moment: datetime) -> str | None:
    value = timeline[0][1]
    for t, v in timeline:
        if t > moment:
            break
        value = v
    return value


def _build_segments(ticket: Ticket, history: list[TicketHistory], calc_end: datetime) -> list[_Segment]:
    """Combina a linha do tempo de equipe e de status em segmentos (ativo/pausado)."""
    team_timeline = _reconstruct_field_timeline(ticket, history, "team_id")
    status_timeline = _reconstruct_field_timeline(ticket, history, "status")

    breakpoints = sorted({t for t, _ in team_timeline} | {t for t, _ in status_timeline})
    breakpoints = [b for b in breakpoints if b < calc_end] or [ticket.created_at]

    segments: list[_Segment] = []
    for i, point in enumerate(breakpoints):
        next_point = breakpoints[i + 1] if i + 1 < len(breakpoints) else calc_end
        team_raw = _value_at(team_timeline, point)
        status_raw = _value_at(status_timeline, point)
        segments.append(
            _Segment(
                start=point,
                end=next_point,
                team_id=int(team_raw) if team_raw not in (None, "None") else None,
                is_paused=(status_raw == _PAUSING_STATUS_VALUE),
            )
        )

    # Segmento final aberto: representa "se nada mudar, o estado atual continua",
    # necessário para projetar o prazo de vencimento para frente.
    last = segments[-1]
    segments.append(_Segment(start=calc_end, end=None, team_id=last.team_id, is_paused=last.is_paused))

    return segments


def _schedules_by_team(session: Session, team_ids: set[int]) -> dict[int, list[TeamSchedule]]:
    return {
        team_id: list(session.exec(select(TeamSchedule).where(TeamSchedule.team_id == team_id)))
        for team_id in team_ids
    }


def _compute_clock(
    target_minutes: int,
    segments: list[_Segment],
    schedules: dict[int, list[TeamSchedule]],
    calc_end: datetime,
    done_at: datetime | None,
    at_risk_threshold_percent: int,
) -> SLAClockResult:
    """Calcula o tempo útil decorrido e o prazo de vencimento de um relógio de SLA."""
    elapsed = 0.0
    for segment in segments:
        if segment.is_paused:
            continue
        windows = expand_schedule(schedules.get(segment.team_id, []))
        segment_end = segment.end if segment.end is not None else calc_end
        elapsed += business_minutes_between(segment.start, segment_end, windows)

    due_at: datetime | None = None
    accumulated = 0.0
    for segment in segments:
        if segment.is_paused:
            continue
        windows = expand_schedule(schedules.get(segment.team_id, []))
        segment_minutes = (
            business_minutes_between(segment.start, segment.end, windows)
            if segment.end is not None
            else float("inf")
        )
        if accumulated + segment_minutes >= target_minutes:
            due_at = add_business_minutes(segment.start, target_minutes - accumulated, windows)
            break
        accumulated += segment_minutes

    if done_at is not None:
        status = SLAClockStatus.MET if elapsed <= target_minutes else SLAClockStatus.BREACHED
    elif due_at is None:
        status = SLAClockStatus.PAUSED
    elif elapsed >= target_minutes:
        status = SLAClockStatus.BREACHED
    elif target_minutes > 0 and (elapsed / target_minutes) * 100 >= at_risk_threshold_percent:
        status = SLAClockStatus.AT_RISK
    else:
        status = SLAClockStatus.PENDING

    return SLAClockResult(
        target_minutes=target_minutes, elapsed_minutes=round(elapsed, 1), status=status, due_at=due_at
    )


def calculate_sla(session: Session, ticket: Ticket) -> dict | None:
    """Calcula os relógios de resposta e solução de um chamado. None se não aplicável."""
    if ticket.status == StatusChamado.CANCELADO:
        return None

    policy = session.exec(select(SLAPolicy).where(SLAPolicy.priority == ticket.priority)).first()
    if policy is None:
        return None

    threshold = get_settings(session).sla_at_risk_threshold_percent

    history = list(session.exec(select(TicketHistory).where(TicketHistory.ticket_id == ticket.id)))

    status_changes = sorted(
        (h for h in history if h.field_name == "status"), key=lambda h: h.changed_at
    )
    first_response_at = next(
        (
            _ensure_utc(h.changed_at)
            for h in status_changes
            if h.old_value == StatusChamado.ABERTO.value
        ),
        None,
    )

    response_calc_end = first_response_at or datetime.now(UTC)
    resolution_calc_end = _ensure_utc(ticket.resolved_at) if ticket.resolved_at else datetime.now(UTC)

    response_segments = _build_segments(ticket, history, response_calc_end)
    resolution_segments = _build_segments(ticket, history, resolution_calc_end)

    team_ids = {
        s.team_id for s in (*response_segments, *resolution_segments) if s.team_id is not None
    }
    schedules = _schedules_by_team(session, team_ids)

    response = _compute_clock(
        policy.response_time_minutes,
        response_segments,
        schedules,
        response_calc_end,
        first_response_at,
        threshold,
    )
    resolution = _compute_clock(
        policy.resolution_time_minutes,
        resolution_segments,
        schedules,
        resolution_calc_end,
        ticket.resolved_at,
        threshold,
    )

    return {"priority": ticket.priority, "response": response, "resolution": resolution}