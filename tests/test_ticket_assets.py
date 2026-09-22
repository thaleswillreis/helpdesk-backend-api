"""Testes de vínculo entre chamados e ativos do CMDB (Tarefa 8.2)."""

from fastapi.testclient import TestClient


def _open_ticket(client, headers_solic, category_id):
    return client.post(
        "/tickets",
        json={
            "title": "Chamado",
            "description": "Descrição.",
            "category_id": category_id,
        },
        headers=headers_solic,
    ).json()


def test_staff_can_link_asset_to_ticket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um técnico deve conseguir vincular um ativo a um chamado."""
    make_user("tec_ta1@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta1@example.com", "senha-forte-123", "solicitante")
    category = make_category("TicketAsset Cat 1")
    headers_tec = auth_headers("tec_ta1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta1@example.com", "senha-forte-123")

    asset = client.post(
        "/assets",
        json={"name": "Notebook A", "asset_type": "notebook"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)

    response = client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": asset["id"]},
        headers=headers_tec,
    )

    assert response.status_code == 201


def test_cannot_link_same_asset_twice(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Vincular o mesmo ativo duas vezes ao mesmo chamado deve retornar 409."""
    make_user("tec_ta2@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta2@example.com", "senha-forte-123", "solicitante")
    category = make_category("TicketAsset Cat 2")
    headers_tec = auth_headers("tec_ta2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta2@example.com", "senha-forte-123")

    asset = client.post(
        "/assets",
        json={"name": "Notebook B", "asset_type": "notebook"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)

    client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": asset["id"]},
        headers=headers_tec,
    )
    response = client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": asset["id"]},
        headers=headers_tec,
    )

    assert response.status_code == 409


def test_suggestions_follow_relationship_graph(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A sugestão deve retornar ativos conectados ao ativo já vinculado, sem vinculá-los."""
    make_user("tec_ta3@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta3@example.com", "senha-forte-123", "solicitante")
    category = make_category("TicketAsset Cat 3")
    headers_tec = auth_headers("tec_ta3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta3@example.com", "senha-forte-123")

    server = client.post(
        "/assets",
        json={"name": "Servidor-Rack-05", "asset_type": "servidor"},
        headers=headers_tec,
    ).json()
    vm = client.post(
        "/assets",
        json={"name": "VM-App-01", "asset_type": "servidor_virtual"},
        headers=headers_tec,
    ).json()
    client.post(
        "/assets/relationships",
        json={
            "from_asset_id": server["id"],
            "to_asset_id": vm["id"],
            "relationship_type": "hospeda",
        },
        headers=headers_tec,
    )

    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": server["id"]},
        headers=headers_tec,
    )

    response = client.get(
        f"/tickets/{ticket['id']}/assets/affected-suggestions", headers=headers_tec
    )

    assert response.status_code == 200
    suggested_ids = [a["id"] for a in response.json()]
    assert vm["id"] in suggested_ids

    # Confirma que a sugestão não vinculou nada de verdade.
    linked = client.get(f"/tickets/{ticket['id']}/assets", headers=headers_tec).json()
    linked_ids = [link["asset_id"] for link in linked]
    assert vm["id"] not in linked_ids


def test_suggestions_exclude_already_linked_assets(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Ativos já vinculados diretamente não devem aparecer na lista de sugestões."""
    make_user("tec_ta4@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta4@example.com", "senha-forte-123", "solicitante")
    category = make_category("TicketAsset Cat 4")
    headers_tec = auth_headers("tec_ta4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta4@example.com", "senha-forte-123")

    nobreak = client.post(
        "/assets",
        json={"name": "Nobreak B", "asset_type": "nobreak"},
        headers=headers_tec,
    ).json()
    server = client.post(
        "/assets",
        json={"name": "Servidor-Rack-06", "asset_type": "servidor"},
        headers=headers_tec,
    ).json()
    client.post(
        "/assets/relationships",
        json={
            "from_asset_id": nobreak["id"],
            "to_asset_id": server["id"],
            "relationship_type": "alimenta",
        },
        headers=headers_tec,
    )

    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": nobreak["id"]},
        headers=headers_tec,
    )
    client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": server["id"]},
        headers=headers_tec,
    )

    response = client.get(
        f"/tickets/{ticket['id']}/assets/affected-suggestions", headers=headers_tec
    )

    assert response.json() == []


def test_solicitante_cannot_link_assets(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante não pode vincular ativos a chamados."""
    make_user("solic_ta5@example.com", "senha-forte-123", "solicitante")
    category = make_category("TicketAsset Cat 5")
    headers = auth_headers("solic_ta5@example.com", "senha-forte-123")

    ticket = _open_ticket(client, headers, category.id)

    response = client.post(
        f"/tickets/{ticket['id']}/assets", json={"asset_id": 1}, headers=headers
    )

    assert response.status_code == 403


def test_admin_can_unlink_asset(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um admin deve conseguir remover o vínculo entre chamado e ativo."""
    make_user("admin_ta1@example.com", "senha-forte-123", "admin")
    make_user("solic_ta6@example.com", "senha-forte-123", "solicitante")
    category = make_category("TicketAsset Cat 6")
    headers_admin = auth_headers("admin_ta1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta6@example.com", "senha-forte-123")

    asset = client.post(
        "/assets",
        json={"name": "Notebook C", "asset_type": "notebook"},
        headers=headers_admin,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(
        f"/tickets/{ticket['id']}/assets",
        json={"asset_id": asset["id"]},
        headers=headers_admin,
    )

    response = client.delete(
        f"/tickets/{ticket['id']}/assets/{asset['id']}", headers=headers_admin
    )

    assert response.status_code == 204
