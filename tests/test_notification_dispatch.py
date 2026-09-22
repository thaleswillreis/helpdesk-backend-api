"""Testes do disparo de eventos de notificação (Tarefa 7.2)."""

from unittest.mock import patch

from sqlmodel import Session

from app.models.enums import WebhookEventType
from app.models.webhook_subscription import WebhookSubscription
from app.services.notification_service import dispatch_event


def test_dispatch_only_notifies_matching_active_subscriptions(
    session: Session, make_user
) -> None:
    """dispatch_event só deve enfileirar para assinaturas ativas que escutam aquele evento."""
    admin = make_user("admin_disp1@example.com", "senha-forte-123", "admin")

    matching = WebhookSubscription(
        url="https://a.example.com",
        secret="s1",
        subscribed_events=["ticket.status_changed"],
        created_by=admin.id,
    )
    wrong_event = WebhookSubscription(
        url="https://b.example.com",
        secret="s2",
        subscribed_events=["ticket.comment_created"],
        created_by=admin.id,
    )
    inactive = WebhookSubscription(
        url="https://c.example.com",
        secret="s3",
        is_active=False,
        subscribed_events=["ticket.status_changed"],
        created_by=admin.id,
    )
    session.add_all([matching, wrong_event, inactive])
    session.commit()

    with patch("app.tasks.webhook_tasks.send_webhook_notification.delay") as mock_delay:
        dispatch_event(
            session, WebhookEventType.TICKET_STATUS_CHANGED, {"foo": "bar"}, ticket_id=1
        )

    assert mock_delay.call_count == 1
    assert mock_delay.call_args[0][0] == matching.id


def test_ticket_status_change_triggers_dispatch(
    client, make_user, make_category, auth_headers
) -> None:
    """Atualizar o status de um chamado deve chamar dispatch_event com o evento correto."""
    make_user("admin_disp2@example.com", "senha-forte-123", "admin")
    make_user("solic_disp2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Dispatch Cat 1")
    headers_admin = auth_headers("admin_disp2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_disp2@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()

    with patch("app.services.ticket_service.dispatch_event") as mock_dispatch:
        client.patch(
            f"/tickets/{ticket['id']}",
            json={"status": "em_atendimento"},
            headers=headers_admin,
        )

    assert mock_dispatch.called
    called_event = mock_dispatch.call_args[0][1]
    assert called_event == WebhookEventType.TICKET_STATUS_CHANGED


def test_public_comment_triggers_dispatch(
    client, make_user, make_category, auth_headers
) -> None:
    """Criar um comentário público deve disparar o evento de comentário criado."""
    make_user("solic_disp3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Dispatch Cat 2")
    headers = auth_headers("solic_disp3@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    with patch("app.services.comment_service.dispatch_event") as mock_dispatch:
        client.post(
            f"/tickets/{ticket['id']}/comments",
            json={"content": "Atualização"},
            headers=headers,
        )

    events = [call.args[1] for call in mock_dispatch.call_args_list]
    assert WebhookEventType.TICKET_COMMENT_CREATED in events


def test_internal_comment_does_not_trigger_comment_event(
    client, make_user, make_category, auth_headers
) -> None:
    """Comentário interno não deve disparar o evento de comentário público."""
    make_user("tec_disp1@example.com", "senha-forte-123", "tecnico")
    category = make_category("Dispatch Cat 3")
    headers = auth_headers("tec_disp1@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    with patch("app.services.comment_service.dispatch_event") as mock_dispatch:
        client.post(
            f"/tickets/{ticket['id']}/comments",
            json={"content": "Nota interna", "is_internal": True},
            headers=headers,
        )

    events = [call.args[1] for call in mock_dispatch.call_args_list]
    assert WebhookEventType.TICKET_COMMENT_CREATED not in events
