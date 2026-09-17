"""Testes do catálogo de serviços (Tarefa 6.1)."""

from fastapi.testclient import TestClient


def test_admin_can_create_catalog_item(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um admin deve conseguir criar um item de catálogo."""
    make_user("admin_cat1@example.com", "senha-forte-123", "admin")
    category = make_category("Catálogo Cat 1")
    headers = auth_headers("admin_cat1@example.com", "senha-forte-123")

    response = client.post(
        "/service-catalog",
        json={
            "name": "Instalação de impressora",
            "description": "Solicitação padrão de instalação.",
            "category_id": category.id,
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["is_active"] is True


def test_non_admin_cannot_create_catalog_item(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um não-admin não pode criar item de catálogo."""
    make_user("tec_cat1@example.com", "senha-forte-123", "tecnico")
    category = make_category("Catálogo Cat 2")
    headers = auth_headers("tec_cat1@example.com", "senha-forte-123")

    response = client.post(
        "/service-catalog",
        json={"name": "Item X", "description": "D", "category_id": category.id},
        headers=headers,
    )

    assert response.status_code == 403


def test_solicitante_does_not_see_inactive_items(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Itens inativos não devem aparecer na listagem para o solicitante."""
    make_user("admin_cat2@example.com", "senha-forte-123", "admin")
    make_user("solic_cat1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo Cat 3")
    headers_admin = auth_headers("admin_cat2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_cat1@example.com", "senha-forte-123")

    item = client.post(
        "/service-catalog",
        json={"name": "Item Ativo", "description": "D", "category_id": category.id},
        headers=headers_admin,
    ).json()
    client.patch(f"/service-catalog/{item['id']}", json={"is_active": False}, headers=headers_admin)

    response = client.get("/service-catalog", headers=headers_solic)

    names = [i["name"] for i in response.json()]
    assert "Item Ativo" not in names


def test_solicitante_gets_404_for_inactive_item_detail(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Acessar o detalhe de um item inativo deve retornar 404 para o solicitante."""
    make_user("admin_cat3@example.com", "senha-forte-123", "admin")
    make_user("solic_cat2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo Cat 4")
    headers_admin = auth_headers("admin_cat3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_cat2@example.com", "senha-forte-123")

    item = client.post(
        "/service-catalog",
        json={"name": "Item Y", "description": "D", "category_id": category.id},
        headers=headers_admin,
    ).json()
    client.patch(f"/service-catalog/{item['id']}", json={"is_active": False}, headers=headers_admin)

    response = client.get(f"/service-catalog/{item['id']}", headers=headers_solic)

    assert response.status_code == 404


def test_catalog_item_with_mismatched_subcategory_returns_422(
    client: TestClient, make_user, auth_headers
) -> None:
    """Subcategoria de outra categoria deve ser rejeitada."""
    make_user("admin_cat4@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_cat4@example.com", "senha-forte-123")

    category_a = client.post(
        "/categories", json={"name": "Cat A Catalog", "default_priority": "media"}, headers=headers
    ).json()
    category_b = client.post(
        "/categories", json={"name": "Cat B Catalog", "default_priority": "media"}, headers=headers
    ).json()
    subcategory_b = client.post(
        "/subcategories",
        json={"name": "Sub B Catalog", "category_id": category_b["id"]},
        headers=headers,
    ).json()

    response = client.post(
        "/service-catalog",
        json={
            "name": "Item Z",
            "description": "D",
            "category_id": category_a["id"],
            "subcategory_id": subcategory_b["id"],
        },
        headers=headers,
    )

    assert response.status_code == 422