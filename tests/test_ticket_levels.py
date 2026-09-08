"""Testes de nível de atendimento e escalonamento (Tarefa 3.3)."""

from fastapi.testclient import TestClient


def _setup_team_and_category(client: TestClient, headers_admin: str) -> tuple[dict, dict]:
    team = client.post("/teams", json={"name": "Equipe Suporte"}, headers=headers_admin).json()
    category = client.post(
        "/categories",
        json={"name": "Sistemas", "default_priority": "media", "default_team_id": team["id"]},
        headers=headers_admin,
    ).json()
    return team, category


def test_ticket_starts_at_level_n1(client: TestClient, make_user, auth_headers) -> None:
    """Um chamado novo deve nascer no nível N1."""
    admin = make_user("admin_lvl1@example.com", "senha-forte-123", "admin")
    headers_admin = auth_headers("admin_lvl1@example.com", "senha-forte-123")
    make_user("solic_lvl1@example.com", "senha-forte-123", "solicitante")
    headers_solic = auth_headers("solic_lvl1@example.com", "senha-forte-123")

    _, category = _setup_team_and_category(client, headers_admin)

    response = client.post(
        "/tickets",
        json={"title": "Erro no sistema", "description": "Falha ao salvar.", "category_id": category["id"]},
        headers=headers_solic,
    )

    assert response.json()["current_level"] == "n1"


def test_can_assign_technician_of_same_level(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um técnico deve conseguir repassar para outro técnico do mesmo nível."""
    make_user("admin_lvl2@example.com", "senha-forte-123", "admin")
    headers_admin = auth_headers("admin_lvl2@example.com", "senha-forte-123")
    tec_a = make_user("tecA_lvl2@example.com", "senha-forte-123", "tecnico", level="n1")
    tec_b = make_user("tecB_lvl2@example.com", "senha-forte-123", "tecnico", level="n1")
    make_user("solic_lvl2@example.com", "senha-forte-123", "solicitante")
    headers_solic = auth_headers("solic_lvl2@example.com", "senha-forte-123")
    headers_tec_a = auth_headers("tecA_lvl2@example.com", "senha-forte-123")

    team, category = _setup_team_and_category(client, headers_admin)
    client.post(f"/teams/{team['id']}/members", json={"user_id": tec_a.id}, headers=headers_admin)
    client.post(f"/teams/{team['id']}/members", json={"user_id": tec_b.id}, headers=headers_admin)

    created = client.post(
        "/tickets",
        json={"title": "Chamado", "description": "Descrição.", "category_id": category["id"]},
        headers=headers_solic,
    ).json()

    response = client.patch(
        f"/tickets/{created['id']}", json={"assigned_to": tec_b.id}, headers=headers_tec_a
    )

    assert response.status_code == 200
    assert response.json()["assigned_to"] == tec_b.id


def test_cannot_assign_technician_of_different_level(
    client: TestClient, make_user, auth_headers
) -> None:
    """Não deve ser possível atribuir a um técnico de nível diferente do chamado."""
    make_user("admin_lvl3@example.com", "senha-forte-123", "admin")
    headers_admin = auth_headers("admin_lvl3@example.com", "senha-forte-123")
    tec_n2 = make_user("tec_n2_lvl3@example.com", "senha-forte-123", "tecnico", level="n2")
    make_user("solic_lvl3@example.com", "senha-forte-123", "solicitante")
    headers_solic = auth_headers("solic_lvl3@example.com", "senha-forte-123")

    team, category = _setup_team_and_category(client, headers_admin)
    client.post(f"/teams/{team['id']}/members", json={"user_id": tec_n2.id}, headers=headers_admin)

    created = client.post(
        "/tickets",
        json={"title": "Chamado", "description": "Descrição.", "category_id": category["id"]},
        headers=headers_solic,
    ).json()

    response = client.patch(
        f"/tickets/{created['id']}", json={"assigned_to": tec_n2.id}, headers=headers_admin
    )

    assert response.status_code == 422


def test_escalating_level_clears_assignment(
    client: TestClient, make_user, auth_headers
) -> None:
    """Escalar de nível deve limpar o técnico atribuído (volta para a fila do novo nível)."""
    make_user("admin_lvl4@example.com", "senha-forte-123", "admin")
    headers_admin = auth_headers("admin_lvl4@example.com", "senha-forte-123")
    tec_n1 = make_user("tec_n1_lvl4@example.com", "senha-forte-123", "tecnico", level="n1")
    make_user("solic_lvl4@example.com", "senha-forte-123", "solicitante")
    headers_solic = auth_headers("solic_lvl4@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_n1_lvl4@example.com", "senha-forte-123")

    team, category = _setup_team_and_category(client, headers_admin)
    client.post(f"/teams/{team['id']}/members", json={"user_id": tec_n1.id}, headers=headers_admin)

    created = client.post(
        "/tickets",
        json={"title": "Chamado", "description": "Descrição.", "category_id": category["id"]},
        headers=headers_solic,
    ).json()
    client.patch(f"/tickets/{created['id']}", json={"assigned_to": tec_n1.id}, headers=headers_admin)

    response = client.patch(
        f"/tickets/{created['id']}", json={"current_level": "n2"}, headers=headers_tec
    )

    assert response.status_code == 200
    assert response.json()["current_level"] == "n2"
    assert response.json()["assigned_to"] is None


def test_technician_cannot_downgrade_level(client: TestClient, make_user, auth_headers) -> None:
    """Um técnico não pode rebaixar o nível de um chamado — só admin."""
    make_user("admin_lvl5@example.com", "senha-forte-123", "admin")
    headers_admin = auth_headers("admin_lvl5@example.com", "senha-forte-123")
    tec_n2 = make_user("tec_n2_lvl5@example.com", "senha-forte-123", "tecnico", level="n2")
    make_user("solic_lvl5@example.com", "senha-forte-123", "solicitante")
    headers_solic = auth_headers("solic_lvl5@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_n2_lvl5@example.com", "senha-forte-123")

    team, category = _setup_team_and_category(client, headers_admin)
    client.post(f"/teams/{team['id']}/members", json={"user_id": tec_n2.id}, headers=headers_admin)

    created = client.post(
        "/tickets",
        json={"title": "Chamado", "description": "Descrição.", "category_id": category["id"]},
        headers=headers_solic,
    ).json()
    client.patch(f"/tickets/{created['id']}", json={"current_level": "n2"}, headers=headers_admin)

    response = client.patch(
        f"/tickets/{created['id']}", json={"current_level": "n1"}, headers=headers_tec
    )

    assert response.status_code == 403


def test_admin_can_downgrade_level(client: TestClient, make_user, auth_headers) -> None:
    """Um admin pode rebaixar o nível de um chamado."""
    make_user("admin_lvl6@example.com", "senha-forte-123", "admin")
    headers_admin = auth_headers("admin_lvl6@example.com", "senha-forte-123")
    make_user("solic_lvl6@example.com", "senha-forte-123", "solicitante")
    headers_solic = auth_headers("solic_lvl6@example.com", "senha-forte-123")

    _, category = _setup_team_and_category(client, headers_admin)

    created = client.post(
        "/tickets",
        json={"title": "Chamado", "description": "Descrição.", "category_id": category["id"]},
        headers=headers_solic,
    ).json()
    client.patch(f"/tickets/{created['id']}", json={"current_level": "n2"}, headers=headers_admin)

    response = client.patch(
        f"/tickets/{created['id']}", json={"current_level": "n1"}, headers=headers_admin
    )

    assert response.status_code == 200
    assert response.json()["current_level"] == "n1"