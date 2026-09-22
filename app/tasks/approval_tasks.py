"""Tarefa periódica do Celery Beat: aplica decisão automática a aprovações expiradas."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.enums import ApprovalTimeoutAction, StatusChamado
from app.models.service_catalog_item import ServiceCatalogItem
from app.models.ticket import Ticket
from app.services.system_user_service import get_system_user
from app.services.ticket_approval_service import approve_ticket


def _ensure_utc(dt: datetime) -> datetime:
    """Normaliza um datetime lido do banco (naive) para UTC-aware."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def apply_approval_timeouts(session: Session) -> None:
    """Lógica de negócio pura: recebe a sessão de fora, para ser testável isoladamente
    (usada tanto pela tarefa do Celery, contra o banco real, quanto diretamente pelos
    testes, contra a sessão transacional de teste)."""
    pending = session.exec(
        select(Ticket).where(
            Ticket.status == StatusChamado.AGUARDANDO_APROVACAO,
            Ticket.catalog_item_id.is_not(None),
        )
    )

    system_user = get_system_user(session)
    now = datetime.now(UTC)

    for ticket in pending:
        item = session.get(ServiceCatalogItem, ticket.catalog_item_id)
        if item is None or item.approval_timeout_hours is None:
            continue

        created_at = _ensure_utc(ticket.created_at)
        deadline = created_at.timestamp() + item.approval_timeout_hours * 3600
        if now.timestamp() < deadline:
            continue

        approved = item.approval_timeout_action == ApprovalTimeoutAction.AUTO_APPROVE
        comment = (
            f"Decisão automática por expiração do prazo de aprovação "
            f"({item.approval_timeout_hours}h sem decisão manual)."
        )
        approve_ticket(session, ticket.id, approved, comment, system_user)


@celery_app.task(name="check_approval_timeouts")
def check_approval_timeouts() -> None:
    """Ponto de entrada do Celery: abre a sessão real e delega à lógica testável."""
    with Session(engine) as session:
        apply_approval_timeouts(session)