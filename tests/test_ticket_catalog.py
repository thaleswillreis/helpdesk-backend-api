"""Testes de abertura de chamado via catálogo de serviços (Tarefa 6.2)."""

from fastapi.testclient import TestClient


def _setup_item_with_fields(client, headers_admin, category_id):
    item = client.post(
        "/service-catalog",
        json={"name": "Novo Notebook", "description": "Solicitação de equipamento.", "category_id": category_id},
        headers=headers_admin,
    ).json()

    field_model = client.post(
        f"/service-catalog/{item['id']}/fields",
        json={"label": "Modelo desejado", "field_type": "text", "is_required": True, "display_order": 1},
        headers=headers_admin,
    ).json()
    field_urgencia = client.post(
        f"/service-catalog/{item['id']}/fields",
        json={
            "label": "Urgência",
            "field_type": "select",
            "is_required": True,
            "options": ["baixa", "media", "alta"],
            "display_order": 2,
        },
        headers=headers_admin,
    ).json()

    return item, field_model, field_urgencia


def test_open_ticket_from_catalog_with_valid_answers(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Abrir chamado via catálogo com respostas válidas deve criar o ticket rastreável."""
    make_user("admin_tc1@example.com", "senha-forte-123", "admin")
    make_user("solic_tc1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo TC 1")
    headers_admin = auth_headers("admin_tc1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tc1@example.com", "senha-forte-123")

    item, field_model, field_urgencia = _setup_item_with_fields(client, headers_admin, category.id)

    response = client.post(
        "/tickets/catalog",
        json={
            "catalog_item_id": item["id"],
            "answers": [
                {"field_id": field_model["id"], "value": "Dell Latitude"},
                {"field_id": field_urgencia["id"], "value": "alta"},
            ],
        },
        headers=headers_solic,
    )

    assert response.status_code == 201
    assert response.json()["catalog_item_id"] == item["id"]


def test_missing_required_field_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Omitir um campo obrigatório deve retornar 422."""
    make_user("admin_tc2@example.com", "senha-forte-123", "admin")
    make_user("solic_tc2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo TC 2")
    headers_admin = auth_headers("admin_tc2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tc2@example.com", "senha-forte-123")

    item, field_model, field_urgencia = _setup_item_with_fields(client, headers_admin, category.id)

    response = client.post(
        "/tickets/catalog",
        json={"catalog_item_id": item["id"], "answers": [{"field_id": field_model["id"], "value": "Dell"}]},
        headers=headers_solic,
    )

    assert response.status_code == 422


def test_invalid_select_option_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Valor fora das opções de um campo 'select' deve retornar 422."""
    make_user("admin_tc3@example.com", "senha-forte-123", "admin")
    make_user("solic_tc3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo TC 3")
    headers_admin = auth_headers("admin_tc3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tc3@example.com", "senha-forte-123")

    item, field_model, field_urgencia = _setup_item_with_fields(client, headers_admin, category.id)

    response = client.post(
        "/tickets/catalog",
        json={
            "catalog_item_id": item["id"],
            "answers": [
                {"field_id": field_model["id"], "value": "Dell"},
                {"field_id": field_urgencia["id"], "value": "urgentissimo"},
            ],
        },
        headers=headers_solic,
    )

    assert response.status_code == 422


def test_invalid_number_value_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Valor não numérico em campo 'number' deve retornar 422."""
    make_user("admin_tc4@example.com", "senha-forte-123", "admin")
    make_user("solic_tc4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo TC 4")
    headers_admin = auth_headers("admin_tc4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tc4@example.com", "senha-forte-123")

    item = client.post(
        "/service-catalog",
        json={"name": "Item Numérico", "description": "D", "category_id": category.id},
        headers=headers_admin,
    ).json()
    field_qty = client.post(
        f"/service-catalog/{item['id']}/fields",
        json={"label": "Quantidade", "field_type": "number", "is_required": True, "display_order": 1},
        headers=headers_admin,
    ).json()

    response = client.post(
        "/tickets/catalog",
        json={"catalog_item_id": item["id"], "answers": [{"field_id": field_qty["id"], "value": "duas"}]},
        headers=headers_solic,
    )

    assert response.status_code == 422


def test_cannot_open_ticket_from_inactive_catalog_item(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Item de catálogo inativo não pode originar nova solicitação."""
    make_user("admin_tc5@example.com", "senha-forte-123", "admin")
    make_user("solic_tc5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo TC 5")
    headers_admin = auth_headers("admin_tc5@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tc5@example.com", "senha-forte-123")

    item = client.post(
        "/service-catalog",
        json={"name": "Item Inativo", "description": "D", "category_id": category.id},
        headers=headers_admin,
    ).json()
    client.patch(f"/service-catalog/{item['id']}", json={"is_active": False}, headers=headers_admin)

    response = client.post(
        "/tickets/catalog", json={"catalog_item_id": item["id"], "answers": []}, headers=headers_solic
    )

    assert response.status_code == 404


def test_read_catalog_answers_returns_labeled_values(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """As respostas devem ser recuperáveis com o rótulo do campo."""
    make_user("admin_tc6@example.com", "senha-forte-123", "admin")
    make_user("solic_tc6@example.com", "senha-forte-123", "solicitante")
    category = make_category("Catálogo TC 6")
    headers_admin = auth_headers("admin_tc6@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tc6@example.com", "senha-forte-123")

    item, field_model, field_urgencia = _setup_item_with_fields(client, headers_admin, category.id)

    ticket = client.post(
        "/tickets/catalog",
        json={
            "catalog_item_id": item["id"],
            "answers": [
                {"field_id": field_model["id"], "value": "Dell Latitude"},
                {"field_id": field_urgencia["id"], "value": "media"},
            ],
        },
        headers=headers_solic,
    ).json()

    response = client.get(f"/tickets/{ticket['id']}/catalog-answers", headers=headers_solic)

    labels = {a["label"]: a["value"] for a in response.json()}
    assert labels["Modelo desejado"] == "Dell Latitude"
    assert labels["Urgência"] == "media"