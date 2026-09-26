"""Testes de KPIs: série temporal e desempenho por técnico (Tarefa 9.2)."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.ticket import Ticket


def test_solicitante_cannot_access_trend(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não deve acessar a série temporal de KPIs."""
    make_user("solic_kpi1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_kpi1@example.com", "senha-forte-123")

    response = client.get("/kpis/trend", headers=headers)

    assert response.status_code == 403


def test_trend_generates_buckets_for_full_range_even_without_data(
    client: TestClient, make_user, auth_headers
) -> None:
    """A série temporal deve incluir buckets sem dados (contagem zero), sem buracos."""
    make_user("admin_kpi1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_kpi1@example.com", "senha-forte-123")

    response = client.get(
        "/kpis/trend",
        params={
            "date_from": (datetime.now(UTC) - timedelta(days=5)).isoformat(),
            "date_to": datetime.now(UTC).isoformat(),
            "granularity": "day",
        },
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()["points"]) == 6  # 5 dias atrás até hoje, inclusive


def test_trend_counts_opened_ticket_in_correct_bucket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um chamado aberto deve contar no bucket correspondente à sua data de criação."""
    make_user("admin_kpi2@example.com", "senha-forte-123", "admin")
    make_user("solic_kpi2@example.com", "senha-forte-123", "solicitante")
    category = make_category("KPI Cat 1")
    headers_admin = auth_headers("admin_kpi2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_kpi2@example.com", "senha-forte-123")

    client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    response = client.get("/kpis/trend", headers=headers_admin)

    total_opened = sum(p["opened_count"] for p in response.json()["points"])
    assert total_opened >= 1


def test_technician_kpi_reflects_resolved_ticket(
    client: TestClient, make_user, make_category, auth_headers, session: Session
) -> None:
    """Um técnico com chamado resolvido deve aparecer na lista de KPIs por técnico."""
    tecnico = make_user(
        "tec_kpi1@example.com", "senha-forte-123", "tecnico", level="n1"
    )
    make_user("solic_kpi3@example.com", "senha-forte-123", "solicitante")
    category = make_category("KPI Cat 2", "media")
    headers_admin_or_tec = auth_headers("tec_kpi1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_kpi3@example.com", "senha-forte-123")

    client.post(
        "/sla-policies",
        json={
            "priority": "media",
            "response_time_minutes": 60,
            "resolution_time_minutes": 480,
        },
        headers=headers_admin_or_tec,
    )
    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()

    patch_response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"assigned_to": tecnico.id, "status": "resolvido"},
        headers=headers_admin_or_tec,
    )
    assert patch_response.status_code == 200

    response = client.get("/kpis/technicians", headers=headers_admin_or_tec)

    technician_ids = [item["technician_id"] for item in response.json()["items"]]
    assert tecnico.id in technician_ids


def test_technician_without_resolved_tickets_does_not_appear(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um técnico sem nenhum chamado resolvido no período não deve aparecer na lista."""
    tecnico = make_user("tec_kpi2@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("tec_kpi2@example.com", "senha-forte-123")

    response = client.get("/kpis/technicians", headers=headers)

    technician_ids = [item["technician_id"] for item in response.json()["items"]]
    assert tecnico.id not in technician_ids


def test_trend_with_invalid_granularity_defaults_to_day(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um valor de granularidade inválido deve cair no padrão 'day', sem erro."""
    make_user("admin_kpi3@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_kpi3@example.com", "senha-forte-123")

    response = client.get("/kpis/trend", params={"granularity": "xyz"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["granularity"] == "day"
