"""Testes do fluxo de aprovação de solicitações via catálogo (Tarefa 6.3)."""

from fastapi.testclient import TestClient


def _setup_item(client, headers_admin, category_id, requires_approval: bool):
    return client.post(
        "/service-catalog",
        json={
            "name": "Novo Notebook",
            "description": "Solicitação de equipamento.",
            "category_id": category_id,
            "requires_approval": requires_approval,
        },
        headers=headers_admin,
    ).json()


def test_ticket_from_item_requiring_approval_starts_pending(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Chamado de item com requires_approval=True deve nascer 'aguardando_aprovacao'."""
    make_user("admin_appr1@example.com", "senha-forte-123", "admin")
    make_user("solic_appr1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 1")
    headers_admin = auth_headers("admin_appr1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr1@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, requires_approval=True)

    response = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    )

    assert response.status_code == 201
    assert response.json()["status"] == "aguardando_aprovacao"


def test_ticket_from_item_without_approval_starts_normally(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Chamado de item sem requires_approval deve nascer 'aberto', como antes."""
    make_user("admin_appr2@example.com", "senha-forte-123", "admin")
    make_user("solic_appr2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 2")
    headers_admin = auth_headers("admin_appr2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr2@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, requires_approval=False)

    response = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    )

    assert response.status_code == 201
    assert response.json()["status"] == "aberto"


def test_admin_can_approve_pending_ticket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um admin deve conseguir aprovar um chamado pendente, movendo para 'aberto'."""
    make_user("admin_appr3@example.com", "senha-forte-123", "admin")
    make_user("solic_appr3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 3")
    headers_admin = auth_headers("admin_appr3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr3@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, requires_approval=True)
    ticket = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/approve",
        json={"approved": True, "comment": "Aprovado pelo gestor."},
        headers=headers_admin,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "aberto"


def test_admin_can_reject_pending_ticket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Rejeitar um chamado pendente deve movê-lo para 'cancelado' e fechar o chamado."""
    make_user("admin_appr4@example.com", "senha-forte-123", "admin")
    make_user("solic_appr4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 4")
    headers_admin = auth_headers("admin_appr4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr4@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, requires_approval=True)
    ticket = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/approve",
        json={"approved": False, "comment": "Orçamento indisponível este trimestre."},
        headers=headers_admin,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelado"
    assert response.json()["closed_at"] is not None


def test_non_admin_cannot_approve(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um técnico não pode aprovar/rejeitar chamados."""
    make_user("admin_appr5@example.com", "senha-forte-123", "admin")
    make_user("tec_appr5@example.com", "senha-forte-123", "tecnico")
    make_user("solic_appr5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 5")
    headers_admin = auth_headers("admin_appr5@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_appr5@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr5@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, requires_approval=True)
    ticket = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/approve", json={"approved": True}, headers=headers_tec
    )

    assert response.status_code == 403


def test_cannot_approve_ticket_not_pending(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Aprovar um chamado que não está aguardando aprovação deve retornar 409."""
    make_user("admin_appr6@example.com", "senha-forte-123", "admin")
    make_user("solic_appr6@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 6")
    headers_admin = auth_headers("admin_appr6@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr6@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, requires_approval=False)
    ticket = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/approve", json={"approved": True}, headers=headers_admin
    )

    assert response.status_code == 409


def test_sla_is_paused_while_awaiting_approval(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """O relógio de SLA deve ficar pausado enquanto o chamado aguarda aprovação."""
    make_user("admin_appr7@example.com", "senha-forte-123", "admin")
    make_user("solic_appr7@example.com", "senha-forte-123", "solicitante")
    category = make_category("Aprovação Cat 7", "media")
    headers_admin = auth_headers("admin_appr7@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_appr7@example.com", "senha-forte-123")

    client.post(
        "/sla-policies",
        json={"priority": "media", "response_time_minutes": 60, "resolution_time_minutes": 480},
        headers=headers_admin,
    )
    item = _setup_item(client, headers_admin, category.id, requires_approval=True)
    ticket = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    ).json()

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers_solic)

    assert response.json()["resolution"]["status"] == "paused"