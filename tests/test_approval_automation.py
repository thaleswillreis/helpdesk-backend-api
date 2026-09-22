"""Testes de aprovação automatizada (Tarefa 7.3)."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.ticket import Ticket
from app.tasks.approval_tasks import apply_approval_timeouts


def _setup_item(client, headers_admin, category_id, **overrides):
    payload = {
        "name": "Novo Notebook",
        "description": "Solicitação de equipamento.",
        "category_id": category_id,
        "requires_approval": True,
    }
    payload.update(overrides)
    return client.post("/service-catalog", json=payload, headers=headers_admin).json()


def test_vip_requester_is_auto_approved(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Item com auto_approve_if_vip deve aprovar automaticamente solicitação de usuário VIP."""
    make_user("admin_aa1@example.com", "senha-forte-123", "admin")
    make_user("solic_aa1@example.com", "senha-forte-123", "solicitante", is_vip=True)
    category = make_category("Auto Aprov Cat 1")
    headers_admin = auth_headers("admin_aa1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_aa1@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, auto_approve_if_vip=True)

    response = client.post(
        "/tickets/catalog",
        json={"catalog_item_id": item["id"], "answers": []},
        headers=headers_solic,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "aberto"


def test_non_vip_requester_still_needs_manual_approval(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Mesmo com auto_approve_if_vip, solicitante não-VIP deve continuar pendente."""
    make_user("admin_aa2@example.com", "senha-forte-123", "admin")
    make_user("solic_aa2@example.com", "senha-forte-123", "solicitante", is_vip=False)
    category = make_category("Auto Aprov Cat 2")
    headers_admin = auth_headers("admin_aa2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_aa2@example.com", "senha-forte-123")

    item = _setup_item(client, headers_admin, category.id, auto_approve_if_vip=True)

    response = client.post(
        "/tickets/catalog",
        json={"catalog_item_id": item["id"], "answers": []},
        headers=headers_solic,
    )

    assert response.json()["status"] == "aguardando_aprovacao"


def test_timeout_hours_requires_action_together(
    client: TestClient, make_user, auth_headers
) -> None:
    """Informar approval_timeout_hours sem approval_timeout_action deve retornar 422."""
    make_user("admin_aa3@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_aa3@example.com", "senha-forte-123")

    response = client.post(
        "/service-catalog",
        json={
            "name": "Item X",
            "description": "D",
            "category_id": 1,
            "requires_approval": True,
            "approval_timeout_hours": 24,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_expired_timeout_triggers_auto_reject(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Chamado com prazo de aprovação expirado deve ser rejeitado automaticamente pela tarefa periódica."""
    make_user("admin_aa4@example.com", "senha-forte-123", "admin")
    make_user("solic_aa4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Auto Aprov Cat 4")
    headers_admin = auth_headers("admin_aa4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_aa4@example.com", "senha-forte-123")

    item = _setup_item(
        client,
        headers_admin,
        category.id,
        approval_timeout_hours=1,
        approval_timeout_action="auto_reject",
    )
    ticket = client.post(
        "/tickets/catalog",
        json={"catalog_item_id": item["id"], "answers": []},
        headers=headers_solic,
    ).json()

    db_ticket = session.get(Ticket, ticket["id"])
    db_ticket.created_at = datetime.now(UTC) - timedelta(hours=2)
    session.add(db_ticket)
    session.commit()

    apply_approval_timeouts(session)

    response = client.get(f"/tickets/{ticket['id']}", headers=headers_admin)
    assert response.json()["status"] == "cancelado"


def test_non_expired_timeout_stays_pending(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Chamado dentro do prazo de aprovação não deve ser afetado pela tarefa periódica."""
    make_user("admin_aa5@example.com", "senha-forte-123", "admin")
    make_user("solic_aa5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Auto Aprov Cat 5")
    headers_admin = auth_headers("admin_aa5@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_aa5@example.com", "senha-forte-123")

    item = _setup_item(
        client,
        headers_admin,
        category.id,
        approval_timeout_hours=48,
        approval_timeout_action="auto_approve",
    )
    ticket = client.post(
        "/tickets/catalog",
        json={"catalog_item_id": item["id"], "answers": []},
        headers=headers_solic,
    ).json()

    apply_approval_timeouts(session)

    response = client.get(f"/tickets/{ticket['id']}", headers=headers_admin)
    assert response.json()["status"] == "aguardando_aprovacao"
