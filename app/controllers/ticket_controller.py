"""Endpoints de gestão de chamados (tickets)."""

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.models.enums import NivelAtendimento, StatusChamado
from app.models.user import User
from app.schemas.article import ArticleRead
from app.schemas.asset import AssetRead
from app.schemas.sla_status import SLAClockRead, TicketSLARead
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.schemas.ticket_approval import TicketApprovalDecision
from app.schemas.ticket_article import (
    TicketArticleCreate,
    TicketArticleRead,
    TicketArticleUpdate,
)
from app.schemas.ticket_asset import TicketAssetCreate, TicketAssetRead
from app.schemas.ticket_attachment import TicketAttachmentDownload, TicketAttachmentRead
from app.schemas.ticket_catalog import TicketCatalogAnswerRead, TicketFromCatalogCreate
from app.schemas.ticket_comment import TicketCommentCreate, TicketCommentRead
from app.schemas.ticket_history import TicketHistoryRead
from app.schemas.ticket_overview import TicketOverviewItem, TicketOverviewPage
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
from app.services.sla_calculation_service import SLAClockStatus, calculate_sla
from app.services.ticket_approval_service import (
    TicketNotFoundError as ApprovalTicketNotFoundError,
    TicketNotPendingApprovalError,
    approve_ticket,
)
from app.services.ticket_article_service import (
    ArticleNotFoundError,
    DuplicateLinkError,
    LinkNotFoundError,
    TicketNotFoundError as ArticleLinkTicketNotFoundError,
    TicketNotYetResolvedError,
    link_article,
    list_linked_articles,
    set_resolution,
    suggest_articles,
    unlink_article,
)
from app.services.ticket_asset_service import (
    AssetNotFoundError,
    DuplicateLinkError as AssetDuplicateLinkError,
    LinkNotFoundError as AssetLinkNotFoundError,
    TicketNotFoundError as AssetLinkTicketNotFoundError,
    link_asset,
    list_linked_assets,
    suggest_affected_assets,
    unlink_asset,
)
from app.services.ticket_catalog_service import (
    CatalogItemNotFoundError,
    InvalidAnswerValueError,
    MissingRequiredAnswerError,
    UnknownFieldError,
    create_ticket_from_catalog,
    get_catalog_answers,
)
from app.services.ticket_overview_service import get_tickets_overview
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except (
        InvalidRequesterError,
        CategoryNotFoundError,
        SubcategoryMismatchError,
    ) as exc:
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


@router.post("/catalog", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def add_ticket_from_catalog(
    data: TicketFromCatalogCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketRead:
    """Abre um chamado a partir de um item do catálogo de serviços, validando o formulário."""
    try:
        ticket = create_ticket_from_catalog(session, data, current_user)
    except CatalogItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (
        MissingRequiredAnswerError,
        InvalidAnswerValueError,
        UnknownFieldError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except ForbiddenTicketAccessError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except InvalidRequesterError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketRead.model_validate(ticket)


@router.get("/overview", response_model=TicketOverviewPage)
def read_tickets_overview(
    status_filter: list[StatusChamado] | None = Query(default=None, alias="status"),
    team_id: int | None = None,
    current_level: NivelAtendimento | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sla_status: SLAClockStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> TicketOverviewPage:
    """Lista chamados com filtros combinados (status, equipe, nível, data, SLA).

    Ferramenta de monitoramento para a equipe. Restrito a admin/tecnico.
    """
    total, results = get_tickets_overview(
        session,
        status_filter=status_filter,
        team_id=team_id,
        current_level=current_level,
        created_from=created_from,
        created_to=created_to,
        sla_status=sla_status,
        skip=skip,
        limit=limit,
    )

    items = [
        TicketOverviewItem(
            **TicketRead.model_validate(ticket).model_dump(),
            sla_applicable=sla is not None,
            sla_response=SLAClockRead(**sla["response"].__dict__) if sla else None,
            sla_resolution=SLAClockRead(**sla["resolution"].__dict__) if sla else None,
        )
        for ticket, sla in results
    ]

    return TicketOverviewPage(total=total, skip=skip, limit=limit, items=items)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenLevelDowngradeError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
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


@router.post("/{ticket_id}/approve", response_model=TicketRead)
def approve_or_reject_ticket(
    ticket_id: int,
    data: TicketApprovalDecision,
    session: Session = Depends(get_session),
    admin: User = Depends(require_role("admin")),
) -> TicketRead:
    """Aprova ou rejeita um chamado que está aguardando aprovação. Restrito a administradores."""
    try:
        ticket = approve_ticket(session, ticket_id, data.approved, data.comment, admin)
    except ApprovalTicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except TicketNotPendingApprovalError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return TicketRead.model_validate(ticket)


@router.get(
    "/{ticket_id}/catalog-answers", response_model=list[TicketCatalogAnswerRead]
)
def read_catalog_answers(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TicketCatalogAnswerRead]:
    """Consulta as respostas do formulário de catálogo de um chamado."""
    get_ticket(session, ticket_id, current_user)  # valida visibilidade (levanta 404)
    answers = get_catalog_answers(session, ticket_id)
    return [TicketCatalogAnswerRead(**a) for a in answers]


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [TicketHistoryRead.model_validate(entry) for entry in history]


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ForbiddenInternalCommentError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
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
    "/{ticket_id}/attachments/{attachment_id}/download",
    response_model=TicketAttachmentDownload,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return TicketAttachmentDownload(download_url=url)


@router.get("/{ticket_id}/sla", response_model=TicketSLARead)
def read_ticket_sla(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TicketSLARead:
    """Consulta o status de SLA (resposta e solução) de um chamado."""
    try:
        ticket = get_ticket(session, ticket_id, current_user)
    except TicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    result = calculate_sla(session, ticket)
    if result is None:
        return TicketSLARead(applicable=False)

    return TicketSLARead(
        applicable=True,
        priority=result["priority"],
        response=SLAClockRead(**result["response"].__dict__),
        resolution=SLAClockRead(**result["resolution"].__dict__),
    )


@router.post(
    "/{ticket_id}/articles",
    response_model=TicketArticleRead,
    status_code=status.HTTP_201_CREATED,
)
def add_ticket_article(
    ticket_id: int,
    data: TicketArticleCreate,
    session: Session = Depends(get_session),
    staff: User = Depends(require_role("admin", "tecnico")),
) -> TicketArticleRead:
    """Vincula um artigo a um chamado. Restrito a admin/tecnico."""
    try:
        link = link_article(session, ticket_id, data.article_id, staff)
    except ArticleLinkTicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ArticleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DuplicateLinkError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return TicketArticleRead.model_validate(link)


@router.get("/{ticket_id}/articles", response_model=list[TicketArticleRead])
def read_ticket_articles(
    ticket_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TicketArticleRead]:
    """Lista os artigos vinculados a um chamado."""
    try:
        links = list_linked_articles(session, ticket_id, current_user)
    except ArticleLinkTicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [TicketArticleRead.model_validate(link) for link in links]


@router.get("/{ticket_id}/articles/suggestions", response_model=list[ArticleRead])
def read_article_suggestions(
    ticket_id: int,
    limit: int = 10,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ArticleRead]:
    """Sugere artigos relevantes (mesma categoria + relevância textual) para o chamado."""
    try:
        articles = suggest_articles(session, ticket_id, current_user, limit=limit)
    except ArticleLinkTicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [ArticleRead.model_validate(a) for a in articles]


@router.patch("/{ticket_id}/articles/{article_id}", response_model=TicketArticleRead)
def edit_ticket_article(
    ticket_id: int,
    article_id: int,
    data: TicketArticleUpdate,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> TicketArticleRead:
    """Marca ou desmarca um artigo vinculado como a solução do chamado."""
    try:
        link = set_resolution(session, ticket_id, article_id, data.is_resolution)
    except LinkNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except TicketNotYetResolvedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TicketArticleRead.model_validate(link)


@router.delete(
    "/{ticket_id}/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_ticket_article(
    ticket_id: int,
    article_id: int,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> None:
    """Remove o vínculo entre um chamado e um artigo."""
    try:
        unlink_article(session, ticket_id, article_id)
    except LinkNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/{ticket_id}/assets", response_model=TicketAssetRead, status_code=status.HTTP_201_CREATED
)
def add_ticket_asset(
    ticket_id: int,
    data: TicketAssetCreate,
    session: Session = Depends(get_session),
    staff: User = Depends(require_role("admin", "tecnico")),
) -> TicketAssetRead:
    """Vincula manualmente um ativo a um chamado. Restrito a admin/tecnico."""
    try:
        link = link_asset(session, ticket_id, data, staff)
    except AssetLinkTicketNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except AssetDuplicateLinkError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return TicketAssetRead.model_validate(link)


@router.get("/{ticket_id}/assets/affected-suggestions", response_model=list[AssetRead])
def read_affected_asset_suggestions(
    ticket_id: int,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> list[AssetRead]:
    """Sugere ativos potencialmente afetados via grafo de dependências. Só leitura."""
    try:
        assets = suggest_affected_assets(session, ticket_id)
    except AssetLinkTicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [AssetRead.model_validate(a) for a in assets]


@router.get("/{ticket_id}/assets", response_model=list[TicketAssetRead])
def read_ticket_assets(
    ticket_id: int,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> list[TicketAssetRead]:
    """Lista os ativos vinculados a um chamado. Restrito a admin/tecnico."""
    try:
        links = list_linked_assets(session, ticket_id)
    except AssetLinkTicketNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [TicketAssetRead.model_validate(link) for link in links]


@router.delete("/{ticket_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ticket_asset(
    ticket_id: int,
    asset_id: int,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> None:
    """Remove o vínculo entre um chamado e um ativo. Restrito a admin/tecnico."""
    try:
        unlink_asset(session, ticket_id, asset_id)
    except AssetLinkNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
