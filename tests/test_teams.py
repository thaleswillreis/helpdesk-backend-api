"""Testes de gestão de equipes e membros (Tarefa 3.1)."""

from fastapi.testclient import TestClient


def test_admin_can_create_team(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir criar uma equipe."""
    make_user("admin_team1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_team1@example.com", "senha-forte-123")

    response = client.post(
        "/teams", json={"name": "Suporte N1", "description": "Primeiro nível"}, headers=headers
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Suporte N1"


def test_non_admin_cannot_create_team(client: TestClient, make_user, auth_headers) -> None:
    """Um não-admin deve receber 403 ao tentar criar equipe."""
    make_user("solic_team1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_team1@example.com", "senha-forte-123")

    response = client.post("/teams", json={"name": "Redes"}, headers=headers)

    assert response.status_code == 403


def test_admin_can_add_technician_to_team(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um admin deve conseguir adicionar um técnico a uma equipe."""
    make_user("admin_team2@example.com", "senha-forte-123", "admin")
    tecnico = make_user("tec_team1@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("admin_team2@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Hardware Team"}, headers=headers).json()
    response = client.post(
        f"/teams/{team['id']}/members", json={"user_id": tecnico.id}, headers=headers
    )

    assert response.status_code == 204

    members = client.get(f"/teams/{team['id']}/members", headers=headers).json()
    assert any(m["id"] == tecnico.id for m in members)


def test_cannot_add_non_technician_to_team(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não pode ser adicionado como membro de equipe."""
    make_user("admin_team3@example.com", "senha-forte-123", "admin")
    solicitante = make_user("solic_team2@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("admin_team3@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Software Team"}, headers=headers).json()
    response = client.post(
        f"/teams/{team['id']}/members", json={"user_id": solicitante.id}, headers=headers
    )

    assert response.status_code == 422


def test_technician_can_belong_to_multiple_teams(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um técnico deve poder pertencer a mais de uma equipe simultaneamente."""
    make_user("admin_team4@example.com", "senha-forte-123", "admin")
    tecnico = make_user("tec_team2@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("admin_team4@example.com", "senha-forte-123")

    team_a = client.post("/teams", json={"name": "Equipe A"}, headers=headers).json()
    team_b = client.post("/teams", json={"name": "Equipe B"}, headers=headers).json()

    client.post(f"/teams/{team_a['id']}/members", json={"user_id": tecnico.id}, headers=headers)
    response = client.post(
        f"/teams/{team_b['id']}/members", json={"user_id": tecnico.id}, headers=headers
    )

    assert response.status_code == 204


def test_admin_can_remove_team_member(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir remover um técnico de uma equipe."""
    make_user("admin_team5@example.com", "senha-forte-123", "admin")
    tecnico = make_user("tec_team3@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("admin_team5@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Equipe C"}, headers=headers).json()
    client.post(f"/teams/{team['id']}/members", json={"user_id": tecnico.id}, headers=headers)

    response = client.delete(f"/teams/{team['id']}/members/{tecnico.id}", headers=headers)

    assert response.status_code == 204

    members = client.get(f"/teams/{team['id']}/members", headers=headers).json()
    assert members == []