"""Teste de sanidade: garante que a API sobe e responde."""

from fastapi.testclient import TestClient


def test_health_check_returns_ok(client: TestClient) -> None:
    """O endpoint /health deve responder 200 com status 'ok'."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}