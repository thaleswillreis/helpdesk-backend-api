"""Testes da API de chamados (Tarefa 2.2)."""

from fastapi.testclient import TestClient


def _ticket_payload(**overrides) -> dict:
    payload = {
        "title": "Impressora não imprime",
        "description": "Fila travada no setor financeiro.",
        "priority": "media",
        "category": "Hardware",
    }
    payload.update(overrides)
    return payload


def test_solicitante_can_open_ticket_for_self(client: TestClient, make_user, auth_headers) -> None:
    """Um solicitante autenticado deve conseguir abrir chamado para si mesmo."""
    make_user("solic1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic1@example.com", "senha-forte-123")

    response = client.post("/tickets", json=_ticket_payload(), headers=headers)

    assert response.status_code == 201
    assert response.json()["status"] == "aberto"


def test_solicitante_cannot_open_ticket_for_another_user(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não pode abrir chamado em nome de outro usuário."""
    make_user("solic2@example.com", "senha-forte-123", "solicitante")
    other = make_user("solic3@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic2@example.com", "senha-forte-123")

    response = client.post(
        "/tickets", json=_ticket_payload(requester_id=other.id), headers=headers
    )

    assert response.status_code == 403


def test_tecnico_can_open_ticket_for_another_user(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um técnico pode abrir chamado em nome de outro usuário (ex.: recebido por telefone)."""
    make_user("tec1@example.com", "senha-forte-123", "tecnico")
    requester = make_user("solic4@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("tec1@example.com", "senha-forte-123")

    response = client.post(
        "/tickets", json=_ticket_payload(requester_id=requester.id), headers=headers
    )

    assert response.status_code == 201
    assert response.json()["requester_id"] == requester.id


def test_solicitante_only_sees_own_tickets(client: TestClient, make_user, auth_headers) -> None:
    """Um solicitante não deve ver chamados de outro usuário na listagem."""
    make_user("solic5@example.com", "senha-forte-123", "solicitante")
    make_user("solic6@example.com", "senha-forte-123", "solicitante")

    headers_a = auth_headers("solic5@example.com", "senha-forte-123")
    headers_b = auth_headers("solic6@example.com", "senha-forte-123")

    client.post("/tickets", json=_ticket_payload(title="Chamado A"), headers=headers_a)
    client.post("/tickets", json=_ticket_payload(title="Chamado B"), headers=headers_b)

    response = client.get("/tickets", headers=headers_a)

    assert response.status_code == 200
    titles = [t["title"] for t in response.json()]
    assert "Chamado A" in titles
    assert "Chamado B" not in titles


def test_solicitante_cannot_view_others_ticket_detail(
    client: TestClient, make_user, auth_headers
) -> None:
    """Acessar o detalhe de chamado de outro solicitante deve retornar 404."""
    make_user("solic7@example.com", "senha-forte-123", "solicitante")
    make_user("solic8@example.com", "senha-forte-123", "solicitante")
    headers_a = auth_headers("solic7@example.com", "senha-forte-123")
    headers_b = auth_headers("solic8@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(), headers=headers_a).json()

    response = client.get(f"/tickets/{created['id']}", headers=headers_b)

    assert response.status_code == 404


def test_solicitante_cannot_update_ticket(client: TestClient, make_user, auth_headers) -> None:
    """Um solicitante não pode atualizar chamados, mesmo o próprio."""
    make_user("solic9@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic9@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(), headers=headers).json()
    response = client.patch(f"/tickets/{created['id']}", json={"status": "fechado"}, headers=headers)

    assert response.status_code == 403


def test_tecnico_updating_status_to_resolvido_sets_resolved_at(
    client: TestClient, make_user, auth_headers
) -> None:
    """Ao mudar status para resolvido, resolved_at deve ser preenchido automaticamente."""
    make_user("tec2@example.com", "senha-forte-123", "tecnico")
    make_user("solic10@example.com", "senha-forte-123", "solicitante")

    headers_solic = auth_headers("solic10@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec2@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(), headers=headers_solic).json()
    response = client.patch(
        f"/tickets/{created['id']}", json={"status": "resolvido"}, headers=headers_tec
    )

    assert response.status_code == 200
    assert response.json()["resolved_at"] is not None
    assert response.json()["closed_at"] is None


def test_updating_status_to_cancelado_sets_closed_at(
    client: TestClient, make_user, auth_headers
) -> None:
    """Cancelado é terminal como fechado: deve preencher closed_at."""
    make_user("tec3@example.com", "senha-forte-123", "tecnico")
    make_user("solic11@example.com", "senha-forte-123", "solicitante")

    headers_solic = auth_headers("solic11@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec3@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(), headers=headers_solic).json()
    response = client.patch(
        f"/tickets/{created['id']}", json={"status": "cancelado"}, headers=headers_tec
    )

    assert response.status_code == 200
    assert response.json()["closed_at"] is not None