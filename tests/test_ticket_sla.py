"""Testes de SLA de chamados (Tarefa 4.2). Manipula created_at direto no banco
para tornar os testes determinísticos, sem depender de tempo real de execução."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.ticket import Ticket


def _setup(client: TestClient, make_user, auth_headers):
    make_user("admin_sla_t1@example.com", "senha-forte-123", "admin")
    make_user("solic_sla_t1@example.com", "senha-forte-123", "solicitante")
    headers_admin = auth_headers("admin_sla_t1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_sla_t1@example.com", "senha-forte-123")

    category = client.post(
        "/categories",
        json={"name": "SLA Test Cat", "default_priority": "media"},
        headers=headers_admin,
    ).json()
    client.post(
        "/sla-policies",
        json={"priority": "media", "response_time_minutes": 60, "resolution_time_minutes": 480},
        headers=headers_admin,
    )

    return headers_admin, headers_solic, category


def test_ticket_without_sla_policy_is_not_applicable(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Sem política cadastrada para a prioridade, o SLA não é aplicável."""
    make_user("solic_sla_np@example.com", "senha-forte-123", "solicitante")
    category = make_category("Sem Politica", "baixa")
    headers = auth_headers("solic_sla_np@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets", json={"title": "T", "description": "D", "category_id": category.id}, headers=headers
    ).json()

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers)

    assert response.json()["applicable"] is False


def test_cancelled_ticket_is_not_applicable(client: TestClient, make_user, auth_headers) -> None:
    """Chamado cancelado não deve ter SLA aplicável, mesmo com política cadastrada."""
    headers_admin, headers_solic, category = _setup(client, make_user, auth_headers)

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category["id"]},
        headers=headers_solic,
    ).json()
    client.patch(f"/tickets/{ticket['id']}", json={"status": "cancelado"}, headers=headers_admin)

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers_solic)

    assert response.json()["applicable"] is False


def test_fresh_ticket_response_is_pending_with_due_at_in_future(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um chamado recém-criado (equipe 24/7) deve ter resposta pendente com prazo futuro."""
    headers_admin, headers_solic, category = _setup(client, make_user, auth_headers)

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category["id"]},
        headers=headers_solic,
    ).json()

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers_solic)
    body = response.json()

    assert body["applicable"] is True
    assert body["response"]["status"] == "pending"
    assert body["response"]["due_at"] is not None


def test_response_met_when_status_changes_before_deadline(
    client: TestClient, make_user, auth_headers, session: Session
) -> None:
    """Se o chamado sai de 'aberto' rapidamente, a resposta deve ser 'met'."""
    headers_admin, headers_solic, category = _setup(client, make_user, auth_headers)

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category["id"]},
        headers=headers_solic,
    ).json()
    client.patch(f"/tickets/{ticket['id']}", json={"status": "em_atendimento"}, headers=headers_admin)

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers_solic)

    assert response.json()["response"]["status"] == "met"


def test_resolution_breached_when_created_long_ago(
    client: TestClient, make_user, auth_headers, session: Session
) -> None:
    """Chamado criado há mais tempo que o prazo de solução deve aparecer como 'breached'."""
    headers_admin, headers_solic, category = _setup(client, make_user, auth_headers)

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category["id"]},
        headers=headers_solic,
    ).json()

    # Simula que o chamado foi criado há 10 horas (prazo de solução é 480min = 8h)
    db_ticket = session.get(Ticket, ticket["id"])
    db_ticket.created_at = datetime.now(UTC) - timedelta(hours=10)
    session.add(db_ticket)
    session.commit()

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers_solic)

    assert response.json()["resolution"]["status"] == "breached"


def test_sla_pauses_while_waiting_on_requester(
    client: TestClient, make_user, auth_headers
) -> None:
    """Colocar o chamado em 'aguardando_solicitante' deve pausar o relógio de solução."""
    headers_admin, headers_solic, category = _setup(client, make_user, auth_headers)

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category["id"]},
        headers=headers_solic,
    ).json()
    client.patch(
        f"/tickets/{ticket['id']}", json={"status": "aguardando_solicitante"}, headers=headers_admin
    )

    response = client.get(f"/tickets/{ticket['id']}/sla", headers=headers_solic)

    assert response.json()["resolution"]["status"] == "paused"
    assert response.json()["resolution"]["due_at"] is None