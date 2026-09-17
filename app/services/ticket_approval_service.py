"""Regras de negócio para aprovação/rejeição de chamados."""

from datetime import UTC, datetime

from sqlmodel import Session

from app.models.enums import STATUS_ENCERRADOS, StatusChamado
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
from app.models.user import User


class TicketNotFoundError(Exception):
    """Levantado quando o chamado informado não existe."""


class TicketNotPendingApprovalError(Exception):
    """Levantado quando o chamado não está aguardando aprovação."""


def approve_ticket(
    session: Session, ticket_id: int, approved: bool, comment: str | None, approver: User
) -> Ticket:
    """Aprova ou rejeita um chamado que está aguardando aprovação."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    if ticket.status != StatusChamado.AGUARDANDO_APROVACAO:
        raise TicketNotPendingApprovalError("Este chamado não está aguardando aprovação.")

    old_status = ticket.status
    new_status = StatusChamado.ABERTO if approved else StatusChamado.CANCELADO

    session.add(
        TicketHistory(
            ticket_id=ticket.id,
            field_name="status",
            old_value=old_status.value,
            new_value=new_status.value,
            comment=comment,
            changed_by=approver.id,
        )
    )

    ticket.status = new_status
    now = datetime.now(UTC)
    if new_status in STATUS_ENCERRADOS:
        ticket.closed_at = now
    ticket.updated_at = now

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket