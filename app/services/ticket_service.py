"""Regras de negócio para gestão de chamados (tickets)."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.roles import is_staff
from app.models.enums import STATUS_ENCERRADOS, StatusChamado
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketUpdate


class TicketNotFoundError(Exception):
    """Levantado quando o chamado solicitado não existe (ou não é visível ao usuário)."""


class ForbiddenTicketAccessError(Exception):
    """Levantado quando o usuário não tem permissão para a ação sobre o chamado."""


class InvalidRequesterError(Exception):
    """Levantado quando o solicitante informado não existe ou está inativo."""


class InvalidAssigneeError(Exception):
    """Levantado quando o técnico informado não existe ou está inativo."""


def create_ticket(session: Session, data: TicketCreate, current_user: User) -> Ticket:
    """Cria um chamado. Solicitante abre para si; admin/tecnico pode abrir para outro usuário."""
    requester_id = data.requester_id or current_user.id

    if requester_id != current_user.id:
        if not is_staff(current_user):
            raise ForbiddenTicketAccessError(
                "Você não tem permissão para abrir um chamado em nome de outro usuário."
            )
        requester = session.get(User, requester_id)
        if requester is None or not requester.is_active:
            raise InvalidRequesterError("Solicitante informado não encontrado ou inativo.")

    ticket = Ticket(
        title=data.title,
        description=data.description,
        priority=data.priority,
        category=data.category,
        requester_id=requester_id,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def list_tickets(
    session: Session, current_user: User, skip: int = 0, limit: int = 50
) -> list[Ticket]:
    """Lista chamados: solicitante vê só os próprios; admin/tecnico vê todos."""
    query = select(Ticket)
    if not is_staff(current_user):
        query = query.where(Ticket.requester_id == current_user.id)

    query = query.offset(skip).limit(limit)
    return list(session.exec(query))


def get_ticket(session: Session, ticket_id: int, current_user: User) -> Ticket:
    """Busca um chamado por id, respeitando a visibilidade por papel."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    if not is_staff(current_user) and ticket.requester_id != current_user.id:
        # 404 em vez de 403: não confirma a existência do chamado a quem não pode vê-lo.
        raise TicketNotFoundError("Chamado não encontrado.")

    return ticket


def update_ticket(session: Session, ticket_id: int, data: TicketUpdate) -> Ticket:
    """Atualiza um chamado existente. O controller já restringe isso a admin/tecnico."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    if data.assigned_to is not None:
        technician = session.get(User, data.assigned_to)
        if technician is None or not technician.is_active:
            raise InvalidAssigneeError("Técnico informado não encontrado ou inativo.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    if "status" in update_data:
        now = datetime.now(UTC)
        if ticket.status == StatusChamado.RESOLVIDO and ticket.resolved_at is None:
            ticket.resolved_at = now
        if ticket.status in STATUS_ENCERRADOS and ticket.closed_at is None:
            ticket.closed_at = now

    ticket.updated_at = datetime.now(UTC)

    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket