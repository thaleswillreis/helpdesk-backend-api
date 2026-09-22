"""Disparo de eventos de notificação para assinaturas de webhook ativas."""

from sqlmodel import Session, select

from app.models.enums import WebhookEventType
from app.models.webhook_subscription import WebhookSubscription


def dispatch_event(
    session: Session,
    event_type: WebhookEventType,
    payload: dict,
    ticket_id: int | None = None,
) -> None:
    """Enfileira uma tarefa Celery para cada assinatura ativa interessada neste evento.

    O import de send_webhook_notification é feito aqui dentro (não no topo do
    arquivo) de propósito: evita um import circular, já que celery_app.py
    precisa importar todos os módulos de app/tasks/ (incluindo sla_tasks, que
    depende de sla_notification_service, que depende deste módulo) para o
    worker do Celery reconhecer as tarefas.
    """
    from app.tasks.webhook_tasks import send_webhook_notification

    query = select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True))
    subscriptions = session.exec(query)

    for subscription in subscriptions:
        if event_type.value in subscription.subscribed_events:
            send_webhook_notification.delay(
                subscription.id, event_type.value, payload, ticket_id
            )
