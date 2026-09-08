"""Testes da API de chamados (Tarefa 2.2) e categorização/VIP (Tarefa 2.3)."""

from fastapi.testclient import TestClient


def _ticket_payload(category_id: int, **overrides) -> dict:
    payload = {
        "title": "Impressora não imprime",
        "description": "Fila travada no setor financeiro.",
        "category_id": category_id,
    }
    payload.update(overrides)
    return payload


def test_solicitante_can_open_ticket_for_self(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante autenticado deve conseguir abrir chamado para si mesmo."""
    make_user("solic1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Hardware", "media")
    headers = auth_headers("solic1@example.com", "senha-forte-123")

    response = client.post("/tickets", json=_ticket_payload(category.id), headers=headers)

    assert response.status_code == 201
    assert response.json()["status"] == "aberto"


def test_ticket_uses_category_default_priority_when_not_informed(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Sem prioridade explícita, o chamado deve herdar a prioridade padrão da categoria."""
    make_user("solic2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Sistema de Vendas", "critica")
    headers = auth_headers("solic2@example.com", "senha-forte-123")

    response = client.post("/tickets", json=_ticket_payload(category.id), headers=headers)

    assert response.status_code == 201
    assert response.json()["priority"] == "critica"


def test_explicit_priority_overrides_category_default(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Prioridade informada explicitamente deve prevalecer sobre a padrão da categoria."""
    make_user("solic3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Sistema de Vendas 2", "critica")
    headers = auth_headers("solic3@example.com", "senha-forte-123")

    response = client.post(
        "/tickets", json=_ticket_payload(category.id, priority="baixa"), headers=headers
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "baixa"


def test_vip_requester_always_gets_vip_priority(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Chamado de solicitante VIP deve sempre receber prioridade 'vip', mesmo se outra for pedida."""
    make_user("vip1@example.com", "senha-forte-123", "solicitante", is_vip=True)
    category = make_category("Notebook", "baixa")
    headers = auth_headers("vip1@example.com", "senha-forte-123")

    response = client.post(
        "/tickets", json=_ticket_payload(category.id, priority="baixa"), headers=headers
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "vip"


def test_solicitante_only_sees_own_tickets(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante não deve ver chamados de outro usuário na listagem."""
    make_user("solic5@example.com", "senha-forte-123", "solicitante")
    make_user("solic6@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede")

    headers_a = auth_headers("solic5@example.com", "senha-forte-123")
    headers_b = auth_headers("solic6@example.com", "senha-forte-123")

    client.post("/tickets", json=_ticket_payload(category.id, title="Chamado A"), headers=headers_a)
    client.post("/tickets", json=_ticket_payload(category.id, title="Chamado B"), headers=headers_b)

    response = client.get("/tickets", headers=headers_a)

    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Chamado A" in titles
    assert "Chamado B" not in titles


def test_solicitante_cannot_update_ticket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante não pode atualizar chamados, mesmo o próprio."""
    make_user("solic9@example.com", "senha-forte-123", "solicitante")
    category = make_category("Software")
    headers = auth_headers("solic9@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(category.id), headers=headers).json()
    response = client.patch(f"/tickets/{created['id']}", json={"status": "fechado"}, headers=headers)

    assert response.status_code == 403


def test_tecnico_updating_status_to_resolvido_sets_resolved_at(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Ao mudar status para resolvido, resolved_at deve ser preenchido automaticamente."""
    make_user("tec2@example.com", "senha-forte-123", "tecnico")
    make_user("solic10@example.com", "senha-forte-123", "solicitante")
    category = make_category("Impressora")

    headers_solic = auth_headers("solic10@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec2@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(category.id), headers=headers_solic).json()
    response = client.patch(
        f"/tickets/{created['id']}", json={"status": "resolvido"}, headers=headers_tec
    )

    assert response.status_code == 200
    assert response.json()["resolved_at"] is not None


def test_staff_can_assign_ticket_to_team(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um técnico/admin deve conseguir vincular um chamado a uma equipe."""
    make_user("tec_ticket_team@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ticket_team@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede")
    headers_solic = auth_headers("solic_ticket_team@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_ticket_team@example.com", "senha-forte-123")

    team = client.post(
        "/teams", json={"name": "Equipe Rede"}, headers=headers_tec
    )
    # criar equipe exige admin; caso o técnico não tenha permissão, criamos via admin separado
    if team.status_code == 403:
        make_user("admin_ticket_team@example.com", "senha-forte-123", "admin")
        headers_admin = auth_headers("admin_ticket_team@example.com", "senha-forte-123")
        team = client.post("/teams", json={"name": "Equipe Rede"}, headers=headers_admin)
    team = team.json()

    created = client.post(
        "/tickets", json=_ticket_payload(category.id), headers=headers_solic
    ).json()
    response = client.patch(
        f"/tickets/{created['id']}", json={"team_id": team["id"]}, headers=headers_tec
    )

    assert response.status_code == 200
    assert response.json()["team_id"] == team["id"]


def test_ticket_inherits_team_from_category_default(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um chamado deve nascer com o team_id da equipe padrão da sua categoria."""
    make_user("admin_queue1@example.com", "senha-forte-123", "admin")
    make_user("solic_queue1@example.com", "senha-forte-123", "solicitante")
    headers_admin = auth_headers("admin_queue1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_queue1@example.com", "senha-forte-123")

    team = client.post("/teams", json={"name": "Equipe Redes"}, headers=headers_admin).json()
    category = client.post(
        "/categories",
        json={"name": "Rede/Internet", "default_priority": "alta", "default_team_id": team["id"]},
        headers=headers_admin,
    ).json()

    response = client.post(
        "/tickets",
        json={
            "title": "Sem conexão",
            "description": "Rede caiu no setor comercial.",
            "category_id": category["id"],
        },
        headers=headers_solic,
    )

    assert response.status_code == 201
    assert response.json()["team_id"] == team["id"]


def test_ticket_can_be_reassigned_to_different_team_regardless_of_category(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um chamado deve poder ser reatribuído para qualquer equipe, mesmo fora da categoria original."""
    make_user("admin_queue2@example.com", "senha-forte-123", "admin")
    make_user("tec_queue1@example.com", "senha-forte-123", "tecnico")
    make_user("solic_queue2@example.com", "senha-forte-123", "solicitante")
    headers_admin = auth_headers("admin_queue2@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_queue1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_queue2@example.com", "senha-forte-123")

    team_redes = client.post("/teams", json={"name": "Equipe Redes 2"}, headers=headers_admin).json()
    team_manutencao = client.post(
        "/teams", json={"name": "Equipe Manutenção"}, headers=headers_admin
    ).json()
    category = client.post(
        "/categories",
        json={
            "name": "Rede/Internet 2",
            "default_priority": "alta",
            "default_team_id": team_redes["id"],
        },
        headers=headers_admin,
    ).json()

    created = client.post(
        "/tickets",
        json={
            "title": "Sem conexão",
            "description": "Placa de rede queimada, descoberto após diagnóstico.",
            "category_id": category["id"],
        },
        headers=headers_solic,
    ).json()
    assert created["team_id"] == team_redes["id"]

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"team_id": team_manutencao["id"], "comment": "Placa de rede queimada, escalando para Manutenção."},
        headers=headers_tec,
    )

    assert response.status_code == 200
    assert response.json()["team_id"] == team_manutencao["id"]


def test_category_without_default_team_creates_ticket_without_team(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Categoria sem equipe padrão configurada deve gerar chamado com team_id nulo."""
    make_user("solic_queue3@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_queue3@example.com", "senha-forte-123")
    category = make_category("Sem Equipe Definida")

    response = client.post(
        "/tickets",
        json={
            "title": "Chamado genérico",
            "description": "Categoria ainda sem equipe vinculada.",
            "category_id": category.id,
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["team_id"] is None