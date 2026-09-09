"""Regras de negócio para a listagem de monitoramento de chamados (filtros combinados)."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.enums import NivelAtendimento, StatusChamado
from app.models.ticket import Ticket
from app.services.sla_calculation_service import SLAClockStatus, calculate_sla


def get_tickets_overview(
    session: Session,
    status_filter: list[StatusChamado] | None = None,
    team_id: int | None = None,
    current_level: NivelAtendimento | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sla_status: SLAClockStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, list[tuple[Ticket, dict | None]]]:
    """Lista chamados filtrando por status, equipe, nível, data e situação de SLA.

    NOTA DE PERFORMANCE (registrada para revisão futura, ex.: Fase 7/9): como
    `sla_status` é calculado sob demanda (não é uma coluna indexada), filtrar
    por ele exige calcular o SLA de TODOS os chamados que passam nos demais
    filtros antes de paginar corretamente — aceitável no volume de um projeto
    de portfólio, mas não escala para uma base grande sem materializar o
    status de SLA periodicamente (ex.: via job agendado, quando o Celery
    entrar na Fase 7).
    """
    query = select(Ticket)

    if status_filter:
        query = query.where(Ticket.status.in_(status_filter))
    if team_id is not None:
        query = query.where(Ticket.team_id == team_id)
    if current_level is not None:
        query = query.where(Ticket.current_level == current_level)
    if created_from is not None:
        query = query.where(Ticket.created_at >= created_from)
    if created_to is not None:
        query = query.where(Ticket.created_at <= created_to)

    query = query.order_by(Ticket.created_at.desc())

    if sla_status is None:
        total = len(list(session.exec(query)))
        tickets = list(session.exec(query.offset(skip).limit(limit)))
        return total, [(t, calculate_sla(session, t)) for t in tickets]

    # Com filtro de sla_status: calcula para todos os candidatos antes de paginar.
    all_tickets = list(session.exec(query))
    matched: list[tuple[Ticket, dict | None]] = []
    for ticket in all_tickets:
        sla = calculate_sla(session, ticket)
        resolution_status = sla["resolution"].status if sla else None
        if resolution_status == sla_status:
            matched.append((ticket, sla))

    total = len(matched)
    return total, matched[skip : skip + limit]