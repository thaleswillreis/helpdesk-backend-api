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