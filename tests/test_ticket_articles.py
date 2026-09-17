"""Testes de vínculo entre chamados e artigos (Tarefa 5.3)."""

from fastapi.testclient import TestClient


def _open_ticket(client, headers_solic, category_id, title="Chamado teste"):
    return client.post(
        "/tickets",
        json={"title": title, "description": "Descrição.", "category_id": category_id},
        headers=headers_solic,
    ).json()


def test_staff_can_link_article_to_ticket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um técnico deve conseguir vincular um artigo a um chamado."""
    make_user("tec_ta1@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta1@example.com", "senha-forte-123", "solicitante")
    category = make_category("TA Cat 1")
    headers_tec = auth_headers("tec_ta1@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta1@example.com", "senha-forte-123")

    article = client.post(
        "/articles",
        json={"title": "Artigo A", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)

    response = client.post(
        f"/tickets/{ticket['id']}/articles", json={"article_id": article["id"]}, headers=headers_tec
    )

    assert response.status_code == 201
    assert response.json()["is_resolution"] is False


def test_cannot_link_same_article_twice(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Vincular o mesmo artigo duas vezes ao mesmo chamado deve retornar 409."""
    make_user("tec_ta2@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta2@example.com", "senha-forte-123", "solicitante")
    category = make_category("TA Cat 2")
    headers_tec = auth_headers("tec_ta2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta2@example.com", "senha-forte-123")

    article = client.post(
        "/articles",
        json={"title": "Artigo B", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)

    client.post(f"/tickets/{ticket['id']}/articles", json={"article_id": article["id"]}, headers=headers_tec)
    response = client.post(
        f"/tickets/{ticket['id']}/articles", json={"article_id": article["id"]}, headers=headers_tec
    )

    assert response.status_code == 409


def test_cannot_mark_resolution_before_ticket_resolved(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Marcar um artigo como solução deve falhar se o chamado nunca foi resolvido."""
    make_user("tec_ta3@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta3@example.com", "senha-forte-123", "solicitante")
    category = make_category("TA Cat 3")
    headers_tec = auth_headers("tec_ta3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta3@example.com", "senha-forte-123")

    article = client.post(
        "/articles",
        json={"title": "Artigo C", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(f"/tickets/{ticket['id']}/articles", json={"article_id": article["id"]}, headers=headers_tec)

    response = client.patch(
        f"/tickets/{ticket['id']}/articles/{article['id']}",
        json={"is_resolution": True},
        headers=headers_tec,
    )

    assert response.status_code == 422


def test_can_mark_resolution_after_ticket_resolved(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Marcar um artigo como solução deve funcionar após o chamado ser resolvido."""
    make_user("tec_ta4@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta4@example.com", "senha-forte-123", "solicitante")
    category = make_category("TA Cat 4")
    headers_tec = auth_headers("tec_ta4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta4@example.com", "senha-forte-123")

    article = client.post(
        "/articles",
        json={"title": "Artigo D", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(f"/tickets/{ticket['id']}/articles", json={"article_id": article["id"]}, headers=headers_tec)
    client.patch(f"/tickets/{ticket['id']}", json={"status": "resolvido"}, headers=headers_tec)

    response = client.patch(
        f"/tickets/{ticket['id']}/articles/{article['id']}",
        json={"is_resolution": True},
        headers=headers_tec,
    )

    assert response.status_code == 200
    assert response.json()["is_resolution"] is True


def test_marking_new_resolution_unmarks_previous_one(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Só um artigo pode ser a solução: marcar um novo desmarca o anterior."""
    make_user("tec_ta5@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta5@example.com", "senha-forte-123", "solicitante")
    category = make_category("TA Cat 5")
    headers_tec = auth_headers("tec_ta5@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta5@example.com", "senha-forte-123")

    article_1 = client.post(
        "/articles",
        json={"title": "Artigo E1", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    ).json()
    article_2 = client.post(
        "/articles",
        json={"title": "Artigo E2", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(f"/tickets/{ticket['id']}/articles", json={"article_id": article_1["id"]}, headers=headers_tec)
    client.post(f"/tickets/{ticket['id']}/articles", json={"article_id": article_2["id"]}, headers=headers_tec)
    client.patch(f"/tickets/{ticket['id']}", json={"status": "resolvido"}, headers=headers_tec)

    client.patch(
        f"/tickets/{ticket['id']}/articles/{article_1['id']}",
        json={"is_resolution": True},
        headers=headers_tec,
    )
    client.patch(
        f"/tickets/{ticket['id']}/articles/{article_2['id']}",
        json={"is_resolution": True},
        headers=headers_tec,
    )

    response = client.get(f"/tickets/{ticket['id']}/articles", headers=headers_tec)
    resolutions = [link for link in response.json() if link["is_resolution"]]

    assert len(resolutions) == 1
    assert resolutions[0]["article_id"] == article_2["id"]


def test_solicitante_does_not_see_draft_articles_linked_to_ticket(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Artigos em rascunho vinculados não devem aparecer na listagem para o solicitante."""
    make_user("tec_ta6@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta6@example.com", "senha-forte-123", "solicitante")
    category = make_category("TA Cat 6")
    headers_tec = auth_headers("tec_ta6@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta6@example.com", "senha-forte-123")

    draft_article = client.post(
        "/articles",
        json={"title": "Artigo Rascunho", "content": "C", "category_id": category.id, "status": "draft"},
        headers=headers_tec,
    ).json()
    ticket = _open_ticket(client, headers_solic, category.id)
    client.post(
        f"/tickets/{ticket['id']}/articles", json={"article_id": draft_article["id"]}, headers=headers_tec
    )

    response = client.get(f"/tickets/{ticket['id']}/articles", headers=headers_solic)

    assert response.json() == []


def test_suggestions_prioritize_same_category(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A sugestão deve retornar artigos publicados da mesma categoria do chamado."""
    make_user("tec_ta7@example.com", "senha-forte-123", "tecnico")
    make_user("solic_ta7@example.com", "senha-forte-123", "solicitante")
    category = make_category("Impressora Cat")
    headers_tec = auth_headers("tec_ta7@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_ta7@example.com", "senha-forte-123")

    client.post(
        "/articles",
        json={
            "title": "Como resetar impressora",
            "content": "Procedimento padrão.",
            "category_id": category.id,
            "status": "published",
        },
        headers=headers_tec,
    )
    ticket = _open_ticket(client, headers_solic, category.id, title="Impressora não imprime")

    response = client.get(f"/tickets/{ticket['id']}/articles/suggestions", headers=headers_tec)

    assert response.status_code == 200
    assert any("impressora" in a["title"].lower() for a in response.json())