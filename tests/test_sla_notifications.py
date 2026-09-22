"""Testes da verificação periódica de transições de SLA (Tarefa 7.4)."""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.enums import WebhookEventType
from app.services.sla_notification_service import check_sla_transitions


def _setup_sla(
    client, headers_admin, category_id, response_minutes=60, resolution_minutes=480
):
    client.post(
        "/sla-policies",
        json={
            "priority": "media",
            "response_time_minutes": response_minutes,
            "resolution_time_minutes": resolution_minutes,
        },
        headers=headers_admin,
    )


def test_no_notification_when_status_is_pending(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Um chamado recém-aberto (pending) não deve gerar notificação."""
    make_user("admin_sn1@example.com", "senha-forte-123", "admin")
    make_user("solic_sn1@example.com", "senha-forte-123", "solicitante")
    category = make_category("SLA Notif Cat 1", "media")
    headers_admin = auth_headers("admin_sn1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_sn1@example.com", "senha-forte-123")
    _setup_sla(client, headers_admin, category.id)

    client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    with patch("app.services.sla_notification_service.dispatch_event") as mock_dispatch:
        check_sla_transitions(session)

    assert not mock_dispatch.called


def test_notification_fires_once_on_transition_to_breached(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """A primeira vez que um chamado entra em 'breached' deve disparar notificação."""
    from datetime import UTC, datetime, timedelta

    from app.models.ticket import Ticket

    make_user("admin_sn2@example.com", "senha-forte-123", "admin")
    make_user("solic_sn2@example.com", "senha-forte-123", "solicitante")
    category = make_category("SLA Notif Cat 2", "media")
    headers_admin = auth_headers("admin_sn2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_sn2@example.com", "senha-forte-123")
    _setup_sla(
        client, headers_admin, category.id, response_minutes=60, resolution_minutes=60
    )

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()

    db_ticket = session.get(Ticket, ticket["id"])
    db_ticket.created_at = datetime.now(UTC) - timedelta(hours=3)
    session.add(db_ticket)
    session.commit()

    with patch("app.services.sla_notification_service.dispatch_event") as mock_dispatch:
        check_sla_transitions(session)

    events = [call.args[1] for call in mock_dispatch.call_args_list]
    assert WebhookEventType.TICKET_SLA_BREACHED in events


def test_notification_does_not_repeat_on_second_run_with_same_status(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Rodar a verificação duas vezes seguidas sem mudança de status não deve notificar de novo."""
    from datetime import UTC, datetime, timedelta

    from app.models.ticket import Ticket

    make_user("admin_sn3@example.com", "senha-forte-123", "admin")
    make_user("solic_sn3@example.com", "senha-forte-123", "solicitante")
    category = make_category("SLA Notif Cat 3", "media")
    headers_admin = auth_headers("admin_sn3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_sn3@example.com", "senha-forte-123")
    _setup_sla(
        client, headers_admin, category.id, response_minutes=60, resolution_minutes=60
    )

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()

    db_ticket = session.get(Ticket, ticket["id"])
    db_ticket.created_at = datetime.now(UTC) - timedelta(hours=3)
    session.add(db_ticket)
    session.commit()

    check_sla_transitions(session)  # primeira execução: já deve marcar o estado

    with patch("app.services.sla_notification_service.dispatch_event") as mock_dispatch:
        check_sla_transitions(
            session
        )  # segunda execução: mesmo status, não deve notificar

    assert not mock_dispatch.called


def test_closed_ticket_is_not_checked(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Chamados encerrados (fechado/cancelado) não devem ser avaliados."""
    make_user("admin_sn4@example.com", "senha-forte-123", "admin")
    make_user("solic_sn4@example.com", "senha-forte-123", "solicitante")
    category = make_category("SLA Notif Cat 4", "media")
    headers_admin = auth_headers("admin_sn4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_sn4@example.com", "senha-forte-123")
    _setup_sla(client, headers_admin, category.id)

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()
    client.patch(
        f"/tickets/{ticket['id']}", json={"status": "cancelado"}, headers=headers_admin
    )

    with patch("app.services.sla_notification_service.dispatch_event") as mock_dispatch:
        check_sla_transitions(session)

    assert not mock_dispatch.called
