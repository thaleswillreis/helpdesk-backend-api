"""Testes de comentários e menções (Tarefa 3.4)."""

from fastapi.testclient import TestClient


def test_solicitante_can_create_public_comment(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante deve conseguir comentar publicamente no próprio chamado."""
    make_user("solic_com1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede")
    headers = auth_headers("solic_com1@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Ainda estou com o problema.", "is_internal": False},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["is_internal"] is False


def test_solicitante_cannot_create_internal_comment(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante não pode criar comentário interno."""
    make_user("solic_com2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Software")
    headers = auth_headers("solic_com2@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Nota interna", "is_internal": True},
        headers=headers,
    )

    assert response.status_code == 403


def test_solicitante_does_not_see_internal_comments(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Comentários internos não devem aparecer na listagem para o solicitante."""
    make_user("tec_com1@example.com", "senha-forte-123", "tecnico")
    make_user("solic_com3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Hardware")
    headers_tec = auth_headers("tec_com1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_com3@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    ).json()

    client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Nota interna do time", "is_internal": True},
        headers=headers_tec,
    )
    client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Atualização pública", "is_internal": False},
        headers=headers_tec,
    )

    response = client.get(f"/tickets/{ticket['id']}/comments", headers=headers_solic)

    contents = [c["content"] for c in response.json()]
    assert "Atualização pública" in contents
    assert "Nota interna do time" not in contents


def test_comment_with_mention_registers_mentioned_users(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Mencionar um usuário no comentário deve registrar o vínculo de menção."""
    tecnico = make_user("tec_com2@example.com", "senha-forte-123", "tecnico")
    make_user("solic_com4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede 2")
    headers = auth_headers("solic_com4@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Poderia ajudar?", "mentioned_user_ids": [tecnico.id]},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["mentioned_user_ids"] == [tecnico.id]


def test_mentioning_nonexistent_user_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Mencionar um usuário inexistente deve retornar 422."""
    make_user("solic_com5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Software 2")
    headers = auth_headers("solic_com5@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Oi", "mentioned_user_ids": [999999]},
        headers=headers,
    )

    assert response.status_code == 422