"""Testes de políticas de SLA (Tarefa 4.1)."""

from fastapi.testclient import TestClient


def test_admin_can_create_sla_policy(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir criar uma política de SLA."""
    make_user("admin_sla1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_sla1@example.com", "senha-forte-123")

    response = client.post(
        "/sla-policies",
        json={"priority": "critica", "response_time_minutes": 30, "resolution_time_minutes": 240},
        headers=headers,
    )

    assert response.status_code == 201


def test_cannot_create_duplicate_policy_for_same_priority(
    client: TestClient, make_user, auth_headers
) -> None:
    """Não deve ser possível criar duas políticas para a mesma prioridade."""
    make_user("admin_sla2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_sla2@example.com", "senha-forte-123")

    client.post(
        "/sla-policies",
        json={"priority": "alta", "response_time_minutes": 60, "resolution_time_minutes": 480},
        headers=headers,
    )
    response = client.post(
        "/sla-policies",
        json={"priority": "alta", "response_time_minutes": 30, "resolution_time_minutes": 240},
        headers=headers,
    )

    assert response.status_code == 409


def test_non_admin_cannot_create_sla_policy(client: TestClient, make_user, auth_headers) -> None:
    """Um não-admin não pode criar política de SLA."""
    make_user("tec_sla1@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("tec_sla1@example.com", "senha-forte-123")

    response = client.post(
        "/sla-policies",
        json={"priority": "baixa", "response_time_minutes": 480, "resolution_time_minutes": 2400},
        headers=headers,
    )

    assert response.status_code == 403