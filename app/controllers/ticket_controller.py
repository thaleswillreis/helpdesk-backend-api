"""Endpoints de gestão de chamados (tickets)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.services.ticket_service import (
    ForbiddenTicketAccessError,
    InvalidAssigneeError,
    InvalidRequesterError,
    TicketNotFoundError,
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def open_ticket(
    data: TicketCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    """Abre um novo chamado."""
    try:
        ticket = create_ticket(session, data, current_user)
    except ForbiddenTicketAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidRequesterError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketRead.model_validate(ticket)


@router.get("", response_model=list[TicketRead])
def list_my_tickets(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TicketRead]:
    """Lista chamados visíveis ao usuário autenticado."""
    tickets = list_tickets(session, current_user, skip=skip, limit=limit)
    return [TicketRead.model_validate(ticket) for ticket in tickets]


@router.get("/{ticket_id}", response_model=TicketRead)
def read_ticket(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    """Consulta um chamado específico."""
    try:
        ticket = get_ticket(session, ticket_id, current_user)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return TicketRead.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketRead)
def edit_ticket(
    ticket_id: int,
    data: TicketUpdate,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> TicketRead:
    """Atualiza um chamado. Restrito a admin/tecnico."""
    try:
        ticket = update_ticket(session, ticket_id, data)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAssigneeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketRead.model_validate(ticket)