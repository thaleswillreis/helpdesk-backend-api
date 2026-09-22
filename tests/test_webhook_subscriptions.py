"""Testes de CRUD de assinaturas de webhook (Tarefa 7.2)."""

from fastapi.testclient import TestClient


def test_admin_can_create_subscription(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um admin deve conseguir criar uma assinatura de webhook."""
    make_user("admin_wh1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_wh1@example.com", "senha-forte-123")

    response = client.post(
        "/webhook-subscriptions",
        json={
            "url": "https://example.com/webhook",
            "secret": "supersecretkey123",
            "subscribed_events": ["ticket.status_changed"],
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert "secret" not in response.json()


def test_non_admin_cannot_create_subscription(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um não-admin não pode criar assinatura de webhook."""
    make_user("tec_wh1@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("tec_wh1@example.com", "senha-forte-123")

    response = client.post(
        "/webhook-subscriptions",
        json={
            "url": "https://x.com",
            "secret": "12345678",
            "subscribed_events": ["ticket.assigned"],
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_admin_can_deactivate_subscription(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um admin deve conseguir desativar uma assinatura sem removê-la."""
    make_user("admin_wh2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_wh2@example.com", "senha-forte-123")

    sub = client.post(
        "/webhook-subscriptions",
        json={
            "url": "https://example.com/webhook2",
            "secret": "outrachave123",
            "subscribed_events": ["ticket.comment_created"],
        },
        headers=headers,
    ).json()

    response = client.patch(
        f"/webhook-subscriptions/{sub['id']}",
        json={"is_active": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
