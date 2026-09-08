"""Testes de CRUD de categorias (Tarefa 2.3)."""

from fastapi.testclient import TestClient


def test_admin_can_create_category(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir criar uma categoria."""
    make_user("admin_cat1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_cat1@example.com", "senha-forte-123")

    response = client.post(
        "/categories", json={"name": "Hardware", "default_priority": "media"}, headers=headers
    )

    assert response.status_code == 201
    assert response.json()["default_priority"] == "media"


def test_non_admin_cannot_create_category(client: TestClient, make_user, auth_headers) -> None:
    """Um não-admin deve receber 403 ao tentar criar categoria."""
    make_user("solic_cat1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_cat1@example.com", "senha-forte-123")

    response = client.post(
        "/categories", json={"name": "Rede", "default_priority": "alta"}, headers=headers
    )

    assert response.status_code == 403


def test_any_authenticated_user_can_list_categories(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Qualquer usuário autenticado deve conseguir listar categorias."""
    make_user("solic_cat2@example.com", "senha-forte-123", "solicitante")
    make_category("Software")
    headers = auth_headers("solic_cat2@example.com", "senha-forte-123")

    response = client.get("/categories", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_create_category_with_invalid_team_returns_422(
    client: TestClient, make_user, auth_headers
) -> None:
    """Informar uma equipe inexistente como padrão deve retornar 422."""
    make_user("admin_cat2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_cat2@example.com", "senha-forte-123")

    response = client.post(
        "/categories",
        json={"name": "Categoria X", "default_priority": "baixa", "default_team_id": 9999},
        headers=headers,
    )

    assert response.status_code == 422