"""Regras de negócio para gestão de chamados (tickets)."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.roles import is_admin, is_staff
from app.models.category import Category
from app.models.enums import (
    ORDEM_NIVEL,
    STATUS_ENCERRADOS,
    PrioridadeChamado,
    StatusChamado,
)
from app.models.subcategory import Subcategory
from app.models.team import Team
from app.models.team_membership import TeamMembership
from app.models.ticket import Ticket
from app.models.ticket_history import TicketHistory
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


class TeamNotFoundError(Exception):
    """Levantado quando a equipe informada não existe."""


class InvalidTechnicianLevelError(Exception):
    """Levantado quando o técnico informado não tem o nível esperado para o chamado."""


class TechnicianNotInTeamError(Exception):
    """Levantado quando o técnico informado não é membro da equipe atual do chamado."""


class ForbiddenLevelDowngradeError(Exception):
    """Levantado quando um não-admin tenta rebaixar o nível de um chamado."""


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
    """Cria um chamado, resolvendo solicitante, categoria/subcategoria, prioridade e fila."""
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
        team_id=category.default_team_id,  # Fila automática pela equipe padrão da categoria.
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


# Campos que geram entrada no histórico quando alterados via PATCH.
_TRACKED_FIELDS = (
    "title", "description", "status", "priority",
    "category_id", "subcategory_id", "assigned_to", "team_id", "current_level",
)


def _validate_assignee(session: Session, technician_id: int, ticket: Ticket, final_level) -> User:
    """Valida que o técnico existe, tem o nível esperado e pertence à equipe do chamado."""
    technician = session.get(User, technician_id)
    if technician is None or not technician.is_active:
        raise InvalidAssigneeError("Técnico informado não encontrado ou inativo.")

    if technician.level != final_level:
        raise InvalidTechnicianLevelError(
            f"O técnico precisa estar no nível {final_level.value} para receber este chamado."
        )

    final_team_id = ticket.team_id
    if final_team_id is not None:
        membership = session.get(TeamMembership, (final_team_id, technician_id))
        if membership is None:
            raise TechnicianNotInTeamError(
                "O técnico informado não é membro da equipe atual do chamado."
            )

    return technician


def update_ticket(
    session: Session, ticket_id: int, data: TicketUpdate, current_user: User
) -> Ticket:
    """Atualiza um chamado existente, aplicando as regras de nível/escalonamento."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    if data.category_id is not None and session.get(Category, data.category_id) is None:
        raise CategoryNotFoundError("Categoria informada não encontrada.")

    if data.team_id is not None and session.get(Team, data.team_id) is None:
        raise TeamNotFoundError("Equipe informada não encontrada.")

    update_data = data.model_dump(exclude_unset=True, exclude={"comment"})
    history_entries: list[TicketHistory] = []

    # Resolve o nível final ANTES de validar o técnico, pois a validação depende dele.
    final_level = update_data.get("current_level", ticket.current_level)

    if "current_level" in update_data and update_data["current_level"] != ticket.current_level:
        subindo = ORDEM_NIVEL[update_data["current_level"]] > ORDEM_NIVEL[ticket.current_level]
        if not subindo and not is_admin(current_user):
            raise ForbiddenLevelDowngradeError(
                "Somente um administrador pode rebaixar o nível de um chamado."
            )

        # Ao mudar de nível sem um técnico específico informado junto, o chamado
        # volta para a fila daquele nível (assigned_to é limpo).
        if subindo and "assigned_to" not in update_data and ticket.assigned_to is not None:
            update_data["assigned_to"] = None

    if "assigned_to" in update_data and update_data["assigned_to"] is not None:
        _validate_assignee(session, update_data["assigned_to"], ticket, final_level)

    for field in _TRACKED_FIELDS:
        if field not in update_data:
            continue

        old_value = getattr(ticket, field)
        new_value = update_data[field]

        if old_value == new_value:
            continue

        history_entries.append(
            TicketHistory(
                ticket_id=ticket.id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                comment=data.comment,
                changed_by=current_user.id,
            )
        )
        setattr(ticket, field, new_value)

    if "status" in update_data:
        now = datetime.now(UTC)
        if ticket.status == StatusChamado.RESOLVIDO and ticket.resolved_at is None:
            ticket.resolved_at = now
        if ticket.status in STATUS_ENCERRADOS and ticket.closed_at is None:
            ticket.closed_at = now

    ticket.updated_at = datetime.now(UTC)

    session.add(ticket)
    for entry in history_entries:
        session.add(entry)
    session.commit()
    session.refresh(ticket)
    return ticket


def get_ticket_history(session: Session, ticket_id: int, current_user: User) -> list[TicketHistory]:
    """Lista o histórico de alterações de um chamado, respeitando a mesma visibilidade do detalhe."""
    get_ticket(session, ticket_id, current_user)  # valida existência + visibilidade (levanta 404)

    query = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.changed_at)
    )
    return list(session.exec(query))