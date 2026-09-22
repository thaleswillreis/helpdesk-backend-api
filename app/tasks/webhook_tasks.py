"""Tarefas assíncronas do Celery: entrega de notificações via webhook."""

import hashlib
import hmac
import json

import httpx
from sqlmodel import Session

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.database import engine
from app.models.webhook_delivery import WebhookDelivery
from app.models.webhook_subscription import WebhookSubscription


def _sign_payload(secret: str, body: bytes) -> str:
    """Assina o corpo da requisição via HMAC-SHA256, para o receptor validar a origem."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@celery_app.task(
    name="send_webhook_notification", bind=True, max_retries=3, default_retry_delay=10
)
def send_webhook_notification(
    self, subscription_id: int, event_type: str, payload: dict, ticket_id: int | None
) -> None:
    """Envia o payload assinado para a URL da assinatura e registra o resultado da tentativa.

    Roda em um processo worker separado, por isso abre sua própria sessão de
    banco (Session(engine)) em vez de reutilizar a sessão da requisição HTTP
    que disparou o evento.
    """
    with Session(engine) as session:
        subscription = session.get(WebhookSubscription, subscription_id)
        if subscription is None or not subscription.is_active:
            return

        body = json.dumps({"event": event_type, "data": payload}).encode()
        signature = _sign_payload(subscription.secret, body)

        try:
            response = httpx.post(
                subscription.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                },
                timeout=settings.webhook_timeout_seconds,
            )
            success = response.is_success
            status_code = response.status_code
            error_message = None if success else f"Resposta HTTP {response.status_code}"
        except httpx.RequestError as exc:
            session.add(
                WebhookDelivery(
                    subscription_id=subscription_id,
                    event_type=event_type,
                    ticket_id=ticket_id,
                    success=False,
                    status_code=None,
                    error_message=str(exc),
                )
            )
            session.commit()
            raise self.retry(exc=exc) from exc

        session.add(
            WebhookDelivery(
                subscription_id=subscription_id,
                event_type=event_type,
                ticket_id=ticket_id,
                success=success,
                status_code=status_code,
                error_message=error_message,
            )
        )
        session.commit()
