"""Regras de negócio para gestão de chamados (tickets)."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.roles import is_staff
from app.models.category import Category
from app.models.enums import STATUS_ENCERRADOS, PrioridadeChamado, StatusChamado
from app.models.subcategory import Subcategory
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


class CategoryNotFoundError(Exception):
    """Levantado quando a categoria informada não existe."""


class SubcategoryMismatchError(Exception):
    """Levantado quando a subcategoria informada não pertence à categoria informada."""


def _resolve_requester(session: Session, data: TicketCreate, current_user: User) -> User:
    """Resolve e valida o usuário solicitante do chamado."""
    if data.requester_id is None or data.requester_id == current_user.id:
        return current_user

    if not is_staff(current_user):
        raise ForbiddenTicketAccessError(
            "Você não tem permissão para abrir um chamado em nome de outro usuário."
        )

    requester = session.get(User, data.requester_id)
    if requester is None or not requester.is_active:
        raise InvalidRequesterError("Solicitante informado não encontrado ou inativo.")
    return requester


def _resolve_priority(
    data: TicketCreate, requester: User, category: Category
) -> PrioridadeChamado:
    """Determina a prioridade final: VIP > informada explicitamente > padrão da categoria."""
    if requester.is_vip:
        return PrioridadeChamado.VIP
    if data.priority is not None:
        return data.priority
    return category.default_priority


def create_ticket(session: Session, data: TicketCreate, current_user: User) -> Ticket:
    """Cria um chamado, resolvendo solicitante, categoria/subcategoria e prioridade."""
    requester = _resolve_requester(session, data, current_user)

    category = session.get(Category, data.category_id)
    if category is None:
        raise CategoryNotFoundError("Categoria informada não encontrada.")

    if data.subcategory_id is not None:
        subcategory = session.get(Subcategory, data.subcategory_id)
        if subcategory is None:
            raise CategoryNotFoundError("Subcategoria informada não encontrada.")
        if subcategory.category_id != category.id:
            raise SubcategoryMismatchError(
                "A subcategoria informada não pertence à categoria informada."
            )

    priority = _resolve_priority(data, requester, category)

    ticket = Ticket(
        title=data.title,
        description=data.description,
        priority=priority,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        requester_id=requester.id,
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

    if data.category_id is not None and session.get(Category, data.category_id) is None:
        raise CategoryNotFoundError("Categoria informada não encontrada.")

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