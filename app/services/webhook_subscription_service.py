"""Regras de negócio para assinaturas de webhook."""

from sqlmodel import Session, select

from app.models.user import User
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_subscription import WebhookSubscription
from app.schemas.webhook_subscription import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
)


class WebhookSubscriptionNotFoundError(Exception):
    """Levantado quando a assinatura de webhook informada não existe."""


def create_subscription(
    session: Session, data: WebhookSubscriptionCreate, admin: User
) -> WebhookSubscription:
    """Cria uma assinatura de webhook."""
    subscription = WebhookSubscription(
        url=data.url,
        secret=data.secret,
        subscribed_events=[e.value for e in data.subscribed_events],
        created_by=admin.id,
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def list_subscriptions(session: Session) -> list[WebhookSubscription]:
    """Lista todas as assinaturas de webhook cadastradas."""
    return list(session.exec(select(WebhookSubscription)))


def update_subscription(
    session: Session, subscription_id: int, data: WebhookSubscriptionUpdate
) -> WebhookSubscription:
    """Atualiza uma assinatura de webhook existente."""
    subscription = session.get(WebhookSubscription, subscription_id)
    if subscription is None:
        raise WebhookSubscriptionNotFoundError("Assinatura de webhook não encontrada.")

    update_data = data.model_dump(exclude_unset=True)
    if (
        "subscribed_events" in update_data
        and update_data["subscribed_events"] is not None
    ):
        update_data["subscribed_events"] = [e.value for e in data.subscribed_events]

    for field, value in update_data.items():
        setattr(subscription, field, value)

    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


def delete_subscription(session: Session, subscription_id: int) -> None:
    """Remove uma assinatura de webhook."""
    subscription = session.get(WebhookSubscription, subscription_id)
    if subscription is None:
        raise WebhookSubscriptionNotFoundError("Assinatura de webhook não encontrada.")

    session.delete(subscription)
    session.commit()


def list_deliveries(
    session: Session, subscription_id: int | None = None
) -> list[WebhookDelivery]:
    """Lista o log de tentativas de entrega, opcionalmente filtrando por assinatura."""
    query = select(WebhookDelivery).order_by(WebhookDelivery.attempted_at.desc())
    if subscription_id is not None:
        query = query.where(WebhookDelivery.subscription_id == subscription_id)
    return list(session.exec(query))
