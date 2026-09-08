"""Endpoints de gestão de chamados (tickets)."""

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.schemas.ticket_history import TicketHistoryRead
from app.schemas.ticket_attachment import TicketAttachmentDownload, TicketAttachmentRead
from app.schemas.ticket_comment import TicketCommentCreate, TicketCommentRead
from app.services.attachment_service import (
    AttachmentNotFoundError,
    FileTooLargeError,
    InvalidFileExtensionError,
    TicketNotFoundError as AttachmentTicketNotFoundError,
    get_download_url,
    list_attachments,
    upload_attachment,
)
from app.services.comment_service import (
    ForbiddenInternalCommentError,
    InvalidMentionError,
    TicketNotFoundError as CommentTicketNotFoundError,
    create_comment,
    list_comments,
)
from app.services.ticket_service import (
    CategoryNotFoundError,
    ForbiddenLevelDowngradeError,
    ForbiddenTicketAccessError,
    InvalidAssigneeError,
    InvalidRequesterError,
    InvalidTechnicianLevelError,
    SubcategoryMismatchError,
    TeamNotFoundError,
    TechnicianNotInTeamError,
    TicketNotFoundError,
    create_ticket,
    get_ticket,
    get_ticket_history,
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
    except (InvalidRequesterError, CategoryNotFoundError, SubcategoryMismatchError) as exc:
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
    staff: User = Depends(require_role("admin", "tecnico")),
) -> TicketRead:
    """Atualiza um chamado. Restrito a admin/tecnico."""
    try:
        ticket = update_ticket(session, ticket_id, data, staff)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ForbiddenLevelDowngradeError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except (
        InvalidAssigneeError,
        CategoryNotFoundError,
        TeamNotFoundError,
        InvalidTechnicianLevelError,
        TechnicianNotInTeamError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketRead.model_validate(ticket)


@router.get("/{ticket_id}/history", response_model=list[TicketHistoryRead])
def read_ticket_history(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TicketHistoryRead]:
    """Consulta o histórico de alterações de um chamado."""
    try:
        history = get_ticket_history(session, ticket_id, current_user)
    except TicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [TicketHistoryRead.model_validate(entry) for entry in history]


@router.post(
    "/{ticket_id}/comments", response_model=TicketCommentRead, status_code=status.HTTP_201_CREATED
)
def add_comment(
    ticket_id: int,
    data: TicketCommentCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketCommentRead:
    """Adiciona um comentário (interno ou público) a um chamado."""
    try:
        comment, mentioned_ids = create_comment(session, ticket_id, data, current_user)
    except CommentTicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ForbiddenInternalCommentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except InvalidMentionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketCommentRead(
        id=comment.id,
        ticket_id=comment.ticket_id,
        author_id=comment.author_id,
        content=comment.content,
        is_internal=comment.is_internal,
        created_at=comment.created_at,
        mentioned_user_ids=mentioned_ids,
    )


@router.get("/{ticket_id}/comments", response_model=list[TicketCommentRead])
def read_comments(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TicketCommentRead]:
    """Lista os comentários visíveis ao usuário para um chamado."""
    try:
        comments = list_comments(session, ticket_id, current_user)
    except CommentTicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [TicketCommentRead(**comment) for comment in comments]


@router.post(
    "/{ticket_id}/attachments",
    response_model=TicketAttachmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketAttachmentRead:
    """Envia um anexo para um chamado, armazenando-o no MinIO."""
    file_bytes = await file.read()
    try:
        attachment = upload_attachment(
            session,
            ticket_id,
            file.filename,
            file.content_type or "application/octet-stream",
            file_bytes,
            current_user,
        )
    except AttachmentTicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvalidFileExtensionError, FileTooLargeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketAttachmentRead.model_validate(attachment)


@router.get("/{ticket_id}/attachments", response_model=list[TicketAttachmentRead])
def read_attachments(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TicketAttachmentRead]:
    """Lista os anexos de um chamado."""
    get_ticket(session, ticket_id, current_user)  # valida visibilidade (levanta 404)
    attachments = list_attachments(session, ticket_id)
    return [TicketAttachmentRead.model_validate(a) for a in attachments]


@router.get(
    "/{ticket_id}/attachments/{attachment_id}/download", response_model=TicketAttachmentDownload
)
def download_attachment(
    ticket_id: int,
    attachment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketAttachmentDownload:
    """Gera uma URL de download temporária para o anexo."""
    get_ticket(session, ticket_id, current_user)  # valida visibilidade (levanta 404)
    try:
        url = get_download_url(session, attachment_id)
    except AttachmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return TicketAttachmentDownload(download_url=url)