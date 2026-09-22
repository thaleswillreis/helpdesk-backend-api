"""Testes de ativos e relacionamentos do CMDB (Tarefa 8.1)."""

from fastapi.testclient import TestClient


def test_admin_can_create_asset(client: TestClient, make_user, auth_headers) -> None:
    """Um admin deve conseguir cadastrar um ativo."""
    make_user("admin_asset1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_asset1@example.com", "senha-forte-123")

    response = client.post(
        "/assets",
        json={
            "name": "Notebook Dell 01",
            "asset_type": "notebook",
            "serial_number": "SN-001",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "em_uso"


def test_cannot_create_asset_with_duplicate_serial(
    client: TestClient, make_user, auth_headers
) -> None:
    """Cadastrar um ativo com número de série já usado deve retornar 409."""
    make_user("admin_asset2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_asset2@example.com", "senha-forte-123")

    client.post(
        "/assets",
        json={"name": "Monitor 1", "asset_type": "monitor", "serial_number": "SN-DUP"},
        headers=headers,
    )
    response = client.post(
        "/assets",
        json={"name": "Monitor 2", "asset_type": "monitor", "serial_number": "SN-DUP"},
        headers=headers,
    )

    assert response.status_code == 409


def test_solicitante_cannot_access_assets(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um solicitante não deve acessar o CMDB."""
    make_user("solic_asset1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_asset1@example.com", "senha-forte-123")

    response = client.get("/assets", headers=headers)

    assert response.status_code == 403


def test_create_relationship_between_two_assets(
    client: TestClient, make_user, auth_headers
) -> None:
    """Deve ser possível criar um relacionamento de dependência entre dois ativos."""
    make_user("admin_asset3@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_asset3@example.com", "senha-forte-123")

    server = client.post(
        "/assets",
        json={"name": "Servidor-Rack-03", "asset_type": "servidor"},
        headers=headers,
    ).json()
    vm = client.post(
        "/assets",
        json={"name": "VM-DB-Vendas", "asset_type": "servidor_virtual"},
        headers=headers,
    ).json()

    response = client.post(
        "/assets/relationships",
        json={
            "from_asset_id": server["id"],
            "to_asset_id": vm["id"],
            "relationship_type": "hospeda",
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_cannot_relate_asset_to_itself(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um ativo não pode se relacionar consigo mesmo."""
    make_user("admin_asset4@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_asset4@example.com", "senha-forte-123")

    asset = client.post(
        "/assets", json={"name": "Switch 01", "asset_type": "switch"}, headers=headers
    ).json()

    response = client.post(
        "/assets/relationships",
        json={
            "from_asset_id": asset["id"],
            "to_asset_id": asset["id"],
            "relationship_type": "conectado_a",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_list_relationships_returns_both_directions(
    client: TestClient, make_user, auth_headers
) -> None:
    """A listagem de relacionamentos deve incluir o ativo tanto como origem quanto destino."""
    make_user("admin_asset5@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_asset5@example.com", "senha-forte-123")

    nobreak = client.post(
        "/assets",
        json={"name": "Nobreak Sala TI", "asset_type": "nobreak"},
        headers=headers,
    ).json()
    server = client.post(
        "/assets",
        json={"name": "Servidor-Rack-04", "asset_type": "servidor"},
        headers=headers,
    ).json()

    client.post(
        "/assets/relationships",
        json={
            "from_asset_id": nobreak["id"],
            "to_asset_id": server["id"],
            "relationship_type": "alimenta",
        },
        headers=headers,
    )

    response = client.get(f"/assets/{server['id']}/relationships", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["from_asset_id"] == nobreak["id"]


def test_duplicate_relationship_returns_409(
    client: TestClient, make_user, auth_headers
) -> None:
    """Criar o mesmo relacionamento duas vezes deve retornar 409."""
    make_user("admin_asset6@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_asset6@example.com", "senha-forte-123")

    monitor = client.post(
        "/assets", json={"name": "Monitor X", "asset_type": "monitor"}, headers=headers
    ).json()
    notebook = client.post(
        "/assets",
        json={"name": "Notebook X", "asset_type": "notebook"},
        headers=headers,
    ).json()

    payload = {
        "from_asset_id": monitor["id"],
        "to_asset_id": notebook["id"],
        "relationship_type": "conectado_a",
    }
    client.post("/assets/relationships", json=payload, headers=headers)
    response = client.post("/assets/relationships", json=payload, headers=headers)

    assert response.status_code == 409
