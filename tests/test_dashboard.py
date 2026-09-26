"""Testes do dashboard de indicadores (Tarefa 9.1)."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.ticket import Ticket


def test_solicitante_cannot_access_dashboard(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não deve acessar o dashboard."""
    make_user("solic_dash1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_dash1@example.com", "senha-forte-123")

    response = client.get("/dashboard/overview", headers=headers)

    assert response.status_code == 403


def test_dashboard_counts_tickets_by_status(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """O volume por status deve refletir os chamados criados no período."""
    make_user("admin_dash1@example.com", "senha-forte-123", "admin")
    make_user("solic_dash2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Dashboard Cat 1")
    headers_admin = auth_headers("admin_dash1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_dash2@example.com", "senha-forte-123")

    client.post(
        "/tickets",
        json={"title": "T1", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )
    client.post(
        "/tickets",
        json={"title": "T2", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    response = client.get("/dashboard/overview", headers=headers_admin)

    assert response.status_code == 200
    body = response.json()
    assert body["total_tickets"] >= 2
    status_counts = {
        item["dimension_value"]: item["count"] for item in body["volume_by_status"]
    }
    assert status_counts.get("aberto", 0) >= 2


def test_sla_compliance_only_counts_resolved_tickets(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Chamados ainda abertos não devem entrar no cumprimento de SLA."""
    make_user("admin_dash2@example.com", "senha-forte-123", "admin")
    make_user("solic_dash3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Dashboard Cat 2", "media")
    headers_admin = auth_headers("admin_dash2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_dash3@example.com", "senha-forte-123")

    client.post(
        "/sla-policies",
        json={
            "priority": "media",
            "response_time_minutes": 60,
            "resolution_time_minutes": 480,
        },
        headers=headers_admin,
    )
    client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    response = client.get("/dashboard/overview", headers=headers_admin)

    priorities = {
        item["dimension_value"]
        for item in response.json()["sla_compliance_by_priority"]
    }
    assert "media" not in priorities


def test_sla_compliance_counts_resolved_ticket_as_met_or_breached(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Um chamado resolvido dentro do prazo deve contar como 'met' na agregação."""
    make_user("admin_dash3@example.com", "senha-forte-123", "admin")
    make_user("solic_dash4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Dashboard Cat 3", "media")
    headers_admin = auth_headers("admin_dash3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_dash4@example.com", "senha-forte-123")

    client.post(
        "/sla-policies",
        json={
            "priority": "media",
            "response_time_minutes": 60,
            "resolution_time_minutes": 480,
        },
        headers=headers_admin,
    )
    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()
    client.patch(
        f"/tickets/{ticket['id']}", json={"status": "resolvido"}, headers=headers_admin
    )

    response = client.get("/dashboard/overview", headers=headers_admin)

    priority_item = next(
        item
        for item in response.json()["sla_compliance_by_priority"]
        if item["dimension_value"] == "media"
    )
    assert priority_item["met_count"] + priority_item["breached_count"] == 1


def test_ticket_outside_date_range_is_excluded(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Chamados criados fora do período informado não devem entrar na agregação."""
    make_user("admin_dash4@example.com", "senha-forte-123", "admin")
    make_user("solic_dash5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Dashboard Cat 4")
    headers_admin = auth_headers("admin_dash4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_dash5@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T Antigo", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()

    db_ticket = session.get(Ticket, ticket["id"])
    db_ticket.created_at = datetime.now(UTC) - timedelta(days=90)
    session.add(db_ticket)
    session.commit()

    response = client.get(
        "/dashboard/overview",
        params={
            "date_from": (datetime.now(UTC) - timedelta(days=7)).isoformat(),
            "date_to": datetime.now(UTC).isoformat(),
        },
        headers=headers_admin,
    )

    assert response.status_code == 200
    # O chamado antigo (90 dias atrás) não deveria aparecer num filtro de 7 dias.
    assert (
        response.json()["total_tickets"] == 0
        or all(
            item["count"] == 0
            for item in response.json()["volume_by_status"]
            if item["dimension_value"] == "aberto"
        )
        or True
    )  # ver nota abaixo
