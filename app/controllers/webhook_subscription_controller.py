"""Endpoints de gestão de assinaturas de webhook e seu log de entregas."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.webhook_delivery import WebhookDeliveryRead
from app.schemas.webhook_subscription import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionRead,
    WebhookSubscriptionUpdate,
)
from app.services.webhook_subscription_service import (
    WebhookSubscriptionNotFoundError,
    create_subscription,
    delete_subscription,
    list_deliveries,
    list_subscriptions,
    update_subscription,
)

router = APIRouter(prefix="/webhook-subscriptions", tags=["automation"])


@router.post(
    "", response_model=WebhookSubscriptionRead, status_code=status.HTTP_201_CREATED
)
def add_subscription(
    data: WebhookSubscriptionCreate,
    session: Session = Depends(get_session),
    admin: User = Depends(require_role("admin")),
) -> WebhookSubscriptionRead:
    """Cria uma assinatura de webhook. Restrito a administradores."""
    subscription = create_subscription(session, data, admin)
    return WebhookSubscriptionRead.model_validate(subscription)


@router.get("", response_model=list[WebhookSubscriptionRead])
def get_subscriptions(
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> list[WebhookSubscriptionRead]:
    """Lista as assinaturas de webhook cadastradas. Restrito a administradores."""
    return [
        WebhookSubscriptionRead.model_validate(s) for s in list_subscriptions(session)
    ]


@router.patch("/{subscription_id}", response_model=WebhookSubscriptionRead)
def edit_subscription(
    subscription_id: int,
    data: WebhookSubscriptionUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> WebhookSubscriptionRead:
    """Atualiza uma assinatura de webhook. Restrito a administradores."""
    try:
        subscription = update_subscription(session, subscription_id, data)
    except WebhookSubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return WebhookSubscriptionRead.model_validate(subscription)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_subscription(
    subscription_id: int,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> None:
    """Remove uma assinatura de webhook. Restrito a administradores."""
    try:
        delete_subscription(session, subscription_id)
    except WebhookSubscriptionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/deliveries", response_model=list[WebhookDeliveryRead])
def get_deliveries(
    subscription_id: int | None = None,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> list[WebhookDeliveryRead]:
    """Lista o log de tentativas de entrega de webhook. Restrito a administradores."""
    return [
        WebhookDeliveryRead.model_validate(d)
        for d in list_deliveries(session, subscription_id)
    ]
