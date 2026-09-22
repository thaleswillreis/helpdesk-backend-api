"""Disparo de eventos de notificação para assinaturas de webhook ativas."""

from sqlmodel import Session, select

from app.models.enums import WebhookEventType
from app.models.webhook_subscription import WebhookSubscription
from app.tasks.webhook_tasks import send_webhook_notification


def dispatch_event(
    session: Session,
    event_type: WebhookEventType,
    payload: dict,
    ticket_id: int | None = None,
) -> None:
    """Enfileira uma tarefa Celery para cada assinatura ativa interessada neste evento."""
    query = select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True))
    subscriptions = session.exec(query)

    for subscription in subscriptions:
        if event_type.value in subscription.subscribed_events:
            send_webhook_notification.delay(
                subscription.id, event_type.value, payload, ticket_id
            )
