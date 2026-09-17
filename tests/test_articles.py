"""Testes de artigos da base de conhecimento (Tarefa 5.1)."""

from fastapi.testclient import TestClient


def test_tecnico_can_create_article(client: TestClient, make_user, make_category, auth_headers) -> None:
    """Um técnico deve conseguir criar um artigo."""
    make_user("tec_art1@example.com", "senha-forte-123", "tecnico")
    category = make_category("Rede Art")
    headers = auth_headers("tec_art1@example.com", "senha-forte-123")

    response = client.post(
        "/articles",
        json={"title": "Como resetar o roteador", "content": "Passo a passo...", "category_id": category.id},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_solicitante_cannot_create_article(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante não pode criar artigo."""
    make_user("solic_art1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Software Art")
    headers = auth_headers("solic_art1@example.com", "senha-forte-123")

    response = client.post(
        "/articles",
        json={"title": "T", "content": "C", "category_id": category.id},
        headers=headers,
    )

    assert response.status_code == 403


def test_solicitante_does_not_see_draft_articles(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Artigos em rascunho não devem aparecer na listagem para o solicitante."""
    make_user("tec_art2@example.com", "senha-forte-123", "tecnico")
    make_user("solic_art2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Hardware Art")
    headers_tec = auth_headers("tec_art2@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_art2@example.com", "senha-forte-123")

    client.post(
        "/articles",
        json={"title": "Rascunho", "content": "C", "category_id": category.id, "status": "draft"},
        headers=headers_tec,
    )
    client.post(
        "/articles",
        json={"title": "Publicado", "content": "C", "category_id": category.id, "status": "published"},
        headers=headers_tec,
    )

    response = client.get("/articles", headers=headers_solic)

    titles = [a["title"] for a in response.json()]
    assert "Publicado" in titles
    assert "Rascunho" not in titles


def test_solicitante_gets_404_for_draft_article_detail(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Acessar o detalhe de um artigo em rascunho deve retornar 404 para o solicitante."""
    make_user("tec_art3@example.com", "senha-forte-123", "tecnico")
    make_user("solic_art3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Sistemas Art")
    headers_tec = auth_headers("tec_art3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_art3@example.com", "senha-forte-123")

    article = client.post(
        "/articles",
        json={"title": "Rascunho 2", "content": "C", "category_id": category.id, "status": "draft"},
        headers=headers_tec,
    ).json()

    response = client.get(f"/articles/{article['id']}", headers=headers_solic)

    assert response.status_code == 404


def test_tecnico_can_publish_draft_article(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um técnico deve conseguir publicar um artigo em rascunho."""
    make_user("tec_art4@example.com", "senha-forte-123", "tecnico")
    category = make_category("Rede Art 2")
    headers = auth_headers("tec_art4@example.com", "senha-forte-123")

    article = client.post(
        "/articles",
        json={"title": "T", "content": "C", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.patch(
        f"/articles/{article['id']}", json={"status": "published"}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "published"


def test_article_with_mismatched_subcategory_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Subcategoria de outra categoria deve ser rejeitada."""
    make_user("admin_art1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_art1@example.com", "senha-forte-123")

    category_a = client.post(
        "/categories", json={"name": "Cat A Art", "default_priority": "media"}, headers=headers
    ).json()
    category_b = client.post(
        "/categories", json={"name": "Cat B Art", "default_priority": "media"}, headers=headers
    ).json()
    subcategory_b = client.post(
        "/subcategories",
        json={"name": "Sub B Art", "category_id": category_b["id"]},
        headers=headers,
    ).json()

    response = client.post(
        "/articles",
        json={
            "title": "T",
            "content": "C",
            "category_id": category_a["id"],
            "subcategory_id": subcategory_b["id"],
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_search_finds_article_by_title_stem(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Busca deve encontrar variação de palavra via stemming (plural/singular)."""
    make_user("tec_search1@example.com", "senha-forte-123", "tecnico")
    category = make_category("Search Cat 1")
    headers = auth_headers("tec_search1@example.com", "senha-forte-123")

    client.post(
        "/articles",
        json={
            "title": "Como resetar impressoras da rede",
            "content": "Procedimento padrão.",
            "category_id": category.id,
            "status": "published",
        },
        headers=headers,
    )

    response = client.get("/articles/search?q=impressora", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_finds_article_by_english_term(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Termos técnicos em inglês (ASCII) devem ser encontrados normalmente."""
    make_user("tec_search2@example.com", "senha-forte-123", "tecnico")
    category = make_category("Search Cat 2")
    headers = auth_headers("tec_search2@example.com", "senha-forte-123")

    client.post(
        "/articles",
        json={
            "title": "Configurando o router da rede",
            "content": "Acesse o painel do router via navegador.",
            "category_id": category.id,
            "status": "published",
        },
        headers=headers,
    )

    response = client.get("/articles/search?q=routers", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_matches_tag_exactly(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Tags devem casar por correspondência exata (dicionário simple)."""
    make_user("tec_search3@example.com", "senha-forte-123", "tecnico")
    category = make_category("Search Cat 3")
    headers = auth_headers("tec_search3@example.com", "senha-forte-123")

    client.post(
        "/articles",
        json={
            "title": "Procedimento de rede",
            "content": "Texto genérico sem menção direta ao termo buscado.",
            "tags": ["VPN"],
            "category_id": category.id,
            "status": "published",
        },
        headers=headers,
    )

    response = client.get("/articles/search?q=VPN", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_excludes_draft_articles_for_solicitante(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """A busca não deve retornar artigos em rascunho para o solicitante."""
    make_user("tec_search4@example.com", "senha-forte-123", "tecnico")
    make_user("solic_search1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Search Cat 4")
    headers_tec = auth_headers("tec_search4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_search1@example.com", "senha-forte-123")

    client.post(
        "/articles",
        json={
            "title": "Artigo rascunho sobre servidor",
            "content": "Ainda em elaboração.",
            "category_id": category.id,
            "status": "draft",
        },
        headers=headers_tec,
    )

    response = client.get("/articles/search?q=servidor", headers=headers_solic)

    assert response.status_code == 200
    assert response.json() == []


def test_search_with_no_match_returns_empty_list(
    client: TestClient, make_user, auth_headers
) -> None:
    """Busca sem nenhum resultado deve retornar lista vazia, não erro."""
    make_user("solic_search2@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solic_search2@example.com", "senha-forte-123")

    response = client.get("/articles/search?q=termoquenaoexisteemnenhumlugar", headers=headers)

    assert response.status_code == 200
    assert response.json() == []