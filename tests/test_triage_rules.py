"""Testes do motor de regras de triagem (Tarefa 7.1)."""

from fastapi.testclient import TestClient


def test_admin_can_create_triage_rule(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um admin deve conseguir criar uma regra de triagem."""
    make_user("admin_tr1@example.com", "senha-forte-123", "admin")
    category = make_category("Triagem Cat 1")
    headers = auth_headers("admin_tr1@example.com", "senha-forte-123")

    response = client.post(
        "/triage-rules",
        json={
            "name": "Palavra crítica sobe prioridade",
            "condition_category_id": category.id,
            "condition_keyword": "todos",
            "action_priority": "critica",
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_rule_without_action_returns_422(
    client: TestClient, make_user, auth_headers
) -> None:
    """Uma regra sem nenhuma ação deve ser rejeitada."""
    make_user("admin_tr2@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin_tr2@example.com", "senha-forte-123")

    response = client.post(
        "/triage-rules",
        json={"name": "Regra vazia", "condition_keyword": "teste"},
        headers=headers,
    )

    assert response.status_code == 422


def test_keyword_rule_overrides_default_priority(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um chamado cuja descrição contém a palavra-chave deve ter a prioridade sobrescrita."""
    make_user("admin_tr3@example.com", "senha-forte-123", "admin")
    make_user("solic_tr3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Triagem Cat 2", "baixa")
    headers_admin = auth_headers("admin_tr3@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tr3@example.com", "senha-forte-123")

    client.post(
        "/triage-rules",
        json={
            "name": "Impacto amplo sobe prioridade",
            "condition_keyword": "ninguém consegue",
            "action_priority": "critica",
        },
        headers=headers_admin,
    )

    response = client.post(
        "/tickets",
        json={
            "title": "Sistema fora do ar",
            "description": "Ninguém consegue acessar o sistema de vendas.",
            "category_id": category.id,
        },
        headers=headers_solic,
    )

    assert response.status_code == 201
    assert response.json()["priority"] == "critica"


def test_rule_with_unmatched_category_does_not_apply(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Uma regra restrita a outra categoria não deve afetar chamados de categoria diferente."""
    make_user("admin_tr4@example.com", "senha-forte-123", "admin")
    make_user("solic_tr4@example.com", "senha-forte-123", "solicitante")
    category_a = make_category("Triagem Cat 3", "baixa")
    category_b = make_category("Triagem Cat 4", "baixa")
    headers_admin = auth_headers("admin_tr4@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tr4@example.com", "senha-forte-123")

    client.post(
        "/triage-rules",
        json={
            "name": "Só afeta categoria A",
            "condition_category_id": category_a.id,
            "action_priority": "critica",
        },
        headers=headers_admin,
    )

    response = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category_b.id},
        headers=headers_solic,
    )

    assert response.json()["priority"] == "baixa"


def test_inactive_rule_does_not_apply(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Uma regra inativa não deve ser avaliada."""
    make_user("admin_tr5@example.com", "senha-forte-123", "admin")
    make_user("solic_tr5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Triagem Cat 5", "baixa")
    headers_admin = auth_headers("admin_tr5@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tr5@example.com", "senha-forte-123")

    client.post(
        "/triage-rules",
        json={
            "name": "Regra inativa",
            "is_active": False,
            "condition_keyword": "urgente",
            "action_priority": "critica",
        },
        headers=headers_admin,
    )

    response = client.post(
        "/tickets",
        json={
            "title": "T",
            "description": "Isso é urgente!",
            "category_id": category.id,
        },
        headers=headers_solic,
    )

    assert response.json()["priority"] == "baixa"


def test_later_rule_wins_when_both_match(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Quando duas regras casam e alteram o mesmo campo, a de maior execution_order vence."""
    make_user("admin_tr6@example.com", "senha-forte-123", "admin")
    make_user("solic_tr6@example.com", "senha-forte-123", "solicitante")
    category = make_category("Triagem Cat 6", "baixa")
    headers_admin = auth_headers("admin_tr6@example.com", "senha-forte-123")
    headers_solic = auth_headers("solic_tr6@example.com", "senha-forte-123")

    client.post(
        "/triage-rules",
        json={
            "name": "Regra 1",
            "execution_order": 1,
            "condition_category_id": category.id,
            "action_priority": "media",
        },
        headers=headers_admin,
    )
    client.post(
        "/triage-rules",
        json={
            "name": "Regra 2",
            "execution_order": 2,
            "condition_category_id": category.id,
            "action_priority": "alta",
        },
        headers=headers_admin,
    )

    response = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers_solic,
    )

    assert response.json()["priority"] == "alta"


def test_non_admin_cannot_create_triage_rule(
    client: TestClient, make_user, auth_headers
) -> None:
    """Um não-admin não pode criar regra de triagem."""
    make_user("tec_tr1@example.com", "senha-forte-123", "tecnico")
    headers = auth_headers("tec_tr1@example.com", "senha-forte-123")

    response = client.post(
        "/triage-rules", json={"name": "X", "action_priority": "alta"}, headers=headers
    )

    assert response.status_code == 403
