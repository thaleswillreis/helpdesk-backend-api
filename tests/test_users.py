"""Testes de RBAC e criação de usuário."""

from fastapi.testclient import TestClient
from sqlmodel import Session


def test_admin_can_create_user(client: TestClient, make_user, auth_headers) -> None:
    """Um admin autenticado deve conseguir criar um novo usuário."""
    make_user("admin1@example.com", "senha-forte-123", "admin")
    headers = auth_headers("admin1@example.com", "senha-forte-123")

    response = client.post(
        "/users",
        json={
            "name": "Novo Técnico",
            "email": "tecnico1@example.com",
            "password": "outra-senha-123",
            "role_name": "tecnico",
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["role_name"] == "tecnico"


def test_non_admin_cannot_create_user(client: TestClient, make_user, auth_headers) -> None:
    """Um usuário sem papel admin deve receber 403 ao tentar criar usuário."""
    make_user("solicitante1@example.com", "senha-forte-123", "solicitante")
    headers = auth_headers("solicitante1@example.com", "senha-forte-123")

    response = client.post(
        "/users",
        json={
            "name": "Outro",
            "email": "outro@example.com",
            "password": "senha-123456",
            "role_name": "tecnico",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_create_user_with_duplicate_email_returns_409(
    client: TestClient, make_user, auth_headers, session: Session
) -> None:
    """Criar usuário com email já existente deve retornar 409."""
    make_user("admin2@example.com", "senha-forte-123", "admin")
    make_user("duplicado@example.com", "outra-senha", "solicitante")
    headers = auth_headers("admin2@example.com", "senha-forte-123")

    response = client.post(
        "/users",
        json={
            "name": "Duplicado",
            "email": "duplicado@example.com",
            "password": "senha-123456",
            "role_name": "solicitante",
        },
        headers=headers,
    )

    assert response.status_code == 409