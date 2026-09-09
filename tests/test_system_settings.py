"""Testes de configurações globais do sistema (Tarefa 4.3)."""

from fastapi.testclient import TestClient


def test_default_threshold_is_80_percent(client: TestClient, make_user, auth_headers) -> None:
    """O limiar de risco padrão deve ser 80%."""
    make_user("admin_set1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_set1@example.com", "senha-forte-123")

    response = client.get("/system-settings", headers=headers)

    assert response.status_code == 200
    assert response.json()["sla_at_risk_threshold_percent"] == 80


def test_admin_can_update_threshold(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir atualizar o limiar de risco."""
    make_user("admin_set2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_set2@example.com", "senha-forte-123")

    response = client.patch(
        "/system-settings", json={"sla_at_risk_threshold_percent": 70}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["sla_at_risk_threshold_percent"] == 70


def test_non_admin_cannot_update_threshold(client: TestClient, make_user, auth_headers) -> None:
    """Um técnico não pode alterar as configurações globais."""
    make_user("tec_set1@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("tec_set1@example.com", "senha-forte-123")

    response = client.patch(
        "/system-settings", json={"sla_at_risk_threshold_percent": 50}, headers=headers
    )

    assert response.status_code == 403