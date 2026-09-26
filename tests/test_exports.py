"""Testes de exportação de dados em CSV (Tarefa 9.3)."""

import csv
import io

from fastapi.testclient import TestClient


def test_solicitante_cannot_export_tickets(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não deve conseguir exportar chamados."""
    make_user("solic_exp1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_exp1@example.com", "senha-forte-123")

    response = client.get("/exports/tickets.csv", headers=headers)

    assert response.status_code == 403


def test_export_tickets_returns_valid_csv_with_header(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A exportação de chamados deve retornar um CSV válido com o chamado criado."""
    make_user("admin_exp1@example.com", "senha-forte-123", "admin")
    make_user("solic_exp2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Export Cat 1")
    headers_admin = auth_headers("admin_exp1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_exp2@example.com", "senha-forte-123")

    client.post(
        "/tickets",
        json={"title": "T Export", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    response = client.get("/exports/tickets.csv", headers=headers_admin)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert any(row["title"] == "T Export" for row in rows)


def test_export_dashboard_returns_flattened_csv(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A exportação do dashboard deve retornar seções achatadas em CSV."""
    make_user("admin_exp2@example.com", "senha-forte-123", "admin")
    make_user("solic_exp3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Export Cat 2")
    headers_admin = auth_headers("admin_exp2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_exp3@example.com", "senha-forte-123")

    client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    response = client.get("/exports/dashboard.csv", headers=headers_admin)

    assert response.status_code == 200
    reader = csv.DictReader(io.StringIO(response.text))
    sections = {row["section"] for row in reader}
    assert "volume_by_status" in sections


def test_export_kpi_trend_returns_csv_with_buckets(
    client: TestClient, make_user, auth_headers
) -> None:
    """A exportação da série temporal deve retornar linhas com buckets."""
    make_user("admin_exp3@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_exp3@example.com", "senha-forte-123")

    response = client.get("/exports/kpi-trend.csv", headers=headers)

    assert response.status_code == 200
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) > 0
    assert "bucket" in rows[0]


def test_export_technician_kpis_returns_valid_csv(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A exportação de KPIs por técnico deve incluir o técnico com chamado resolvido."""
    tecnico = make_user(
        "tec_exp1@example.com", "senha-forte-123", "tecnico", level="n1"
    )
    make_user("solic_exp4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Export Cat 3", "media")
    headers_tec = auth_headers("tec_exp1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_exp4@example.com", "senha-forte-123")

    client.post(
        "/sla-policies",
        json={
            "priority": "media",
            "response_time_minutes": 60,
            "resolution_time_minutes": 480,
        },
        headers=headers_tec,
    )
    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()
    client.patch(
        f"/tickets/{ticket['id']}",
        json={"assigned_to": tecnico.id, "status": "resolvido"},
        headers=headers_tec,
    )

    response = client.get("/exports/kpi-technicians.csv", headers=headers_tec)

    assert response.status_code == 200
    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert any(row["technician_id"] == str(tecnico.id) for row in rows)
