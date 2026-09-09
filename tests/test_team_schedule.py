"""Testes de expediente de equipe (Tarefa 4.1)."""

from fastapi.testclient import TestClient


def test_admin_can_add_schedule_entry(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir cadastrar a janela de expediente de um dia."""
    make_user("admin_sched1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_sched1@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Equipe Comercial"}, headers=headers).json()
    response = client.post(
        f"/teams/{team['id']}/schedule",
        json={"weekday": 0, "start_time": "08:00:00", "end_time": "18:00:00"},
        headers=headers,
    )

    assert response.status_code == 201


def test_cannot_duplicate_schedule_for_same_weekday(
    client: TestClient, make_user, auth_headers
) -> None:
    """Não deve permitir duas janelas para o mesmo dia da semana."""
    make_user("admin_sched2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_sched2@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Equipe Telecom"}, headers=headers).json()
    client.post(
        f"/teams/{team['id']}/schedule",
        json={"weekday": 1, "start_time": "08:00:00", "end_time": "18:00:00"},
        headers=headers,
    )
    response = client.post(
        f"/teams/{team['id']}/schedule",
        json={"weekday": 1, "start_time": "09:00:00", "end_time": "17:00:00"},
        headers=headers,
    )

    assert response.status_code == 409


def test_team_without_schedule_returns_empty_list(
    client: TestClient, make_user, auth_headers
) -> None:
    """Uma equipe sem expediente cadastrado (24/7) deve retornar lista vazia."""
    make_user("admin_sched3@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_sched3@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Equipe N2"}, headers=headers).json()
    response = client.get(f"/teams/{team['id']}/schedule", headers=headers)

    assert response.status_code == 200
    assert response.json() == []