"""Verificação periódica de SLA: detecta transições para 'at_risk'/'breached' e notifica."""

from sqlmodel import Session, select

from app.models.enums import STATUS_ENCERRADOS, WebhookEventType
from app.models.sla_notification_state import SlaNotificationState
from app.models.ticket import Ticket
from app.services.notification_service import dispatch_event
from app.services.sla_calculation_service import SLAClockStatus, calculate_sla

_ALERT_STATUSES = {SLAClockStatus.AT_RISK.value, SLAClockStatus.BREACHED.value}

_EVENT_BY_STATUS = {
    SLAClockStatus.AT_RISK.value: WebhookEventType.TICKET_SLA_AT_RISK,
    SLAClockStatus.BREACHED.value: WebhookEventType.TICKET_SLA_BREACHED,
}


def _get_or_create_state(session: Session, ticket_id: int) -> SlaNotificationState:
    state = session.get(SlaNotificationState, ticket_id)
    if state is None:
        state = SlaNotificationState(ticket_id=ticket_id)
        session.add(state)
    return state


def _check_clock_transition(
    session: Session,
    ticket: Ticket,
    clock_name: str,
    current_status: str,
    last_status: str | None,
) -> None:
    """Dispara o webhook se o relógio transicionou para um status de alerta novo."""
    if current_status in _ALERT_STATUSES and current_status != last_status:
        dispatch_event(
            session,
            _EVENT_BY_STATUS[current_status],
            {"ticket_id": ticket.id, "clock": clock_name, "status": current_status},
            ticket_id=ticket.id,
        )


def check_sla_transitions(session: Session) -> None:
    """Varre chamados ativos, calcula o SLA de cada um e notifica transições de risco.

    Lógica de negócio pura, recebendo a sessão de fora — mesma separação já
    usada em apply_approval_timeouts (Tarefa 7.3), para permanecer testável
    sem depender da sessão real de produção que a tarefa Celery abre.
    """
    active_tickets = session.exec(
        select(Ticket).where(Ticket.status.not_in(STATUS_ENCERRADOS))
    )

    for ticket in active_tickets:
        sla = calculate_sla(session, ticket)
        if sla is None:
            continue

        state = _get_or_create_state(session, ticket.id)

        response_status = sla["response"].status.value
        resolution_status = sla["resolution"].status.value

        _check_clock_transition(
            session, ticket, "response", response_status, state.response_last_status
        )
        _check_clock_transition(
            session,
            ticket,
            "resolution",
            resolution_status,
            state.resolution_last_status,
        )

        state.response_last_status = response_status
        state.resolution_last_status = resolution_status
        session.add(state)

    session.commit()
