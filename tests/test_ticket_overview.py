"""Testes da listagem de monitoramento de chamados (Tarefa 4.3)."""

from fastapi.testclient import TestClient


def test_overview_filters_by_status(client: TestClient, make_user, make_category, auth_headers) -> None:
    """A listagem deve filtrar corretamente por status."""
    make_user("admin_ov1@example.com", "senha-forte-123", "admin")
    make_user("solic_ov1@example.com", "senha-forte-123", "solicitante")
    headers_admin = auth_headers("admin_ov1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ov1@example.com", "senha-forte-123")
    category = make_category("Overview Cat")

    ticket = client.post(
        "/tickets",
        json={"title": "T1", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()
    client.patch(f"/tickets/{ticket['id']}", json={"status": "fechado"}, headers=headers_admin)

    response = client.get("/tickets/overview?status=fechado", headers=headers_admin)

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert ticket["id"] in ids


def test_overview_is_forbidden_for_solicitante(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não deve acessar a listagem de monitoramento."""
    make_user("solic_ov2@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_ov2@example.com", "senha-forte-123")

    response = client.get("/tickets/overview", headers=headers)

    assert response.status_code == 403


def test_overview_returns_sla_summary(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Cada item da listagem deve incluir o resumo de SLA calculado."""
    make_user("admin_ov3@example.com", "senha-forte-123", "admin")
    make_user("solic_ov3@example.com", "senha-forte-123", "solicitante")
    headers_admin = auth_headers("admin_ov3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ov3@example.com", "senha-forte-123")
    category = make_category("Overview Cat 2", "media")
    client.post(
        "/sla-policies",
        json={"priority": "media", "response_time_minutes": 60, "resolution_time_minutes": 480},
        headers=headers_admin,
    )

    client.post(
        "/tickets",
        json={"title": "T2", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    response = client.get("/tickets/overview", headers=headers_admin)

    items = response.json()["items"]
    assert any(item["sla_applicable"] for item in items)


def test_overview_pagination_respects_limit(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A paginação deve limitar corretamente a quantidade de itens retornados."""
    make_user("admin_ov4@example.com", "senha-forte-123", "admin")
    make_user("solic_ov4@example.com", "senha-forte-123", "solicitante")
    headers_admin = auth_headers("admin_ov4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ov4@example.com", "senha-forte-123")
    category = make_category("Overview Cat 3")

    for i in range(3):
        client.post(
            "/tickets",
            json={"title": f"T{i}", "description": "D", "category_id": category.id},
            headers=headers_solic,
        )

    response = client.get("/tickets/overview?limit=2", headers=headers_admin)

    assert len(response.json()["items"]) == 2
    assert response.json()["total"] >= 3