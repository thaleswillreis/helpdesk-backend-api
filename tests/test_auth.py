"""Testes do fluxo de autenticação (login e refresh)."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import hash_password
from app.models.user import User


def _create_user(session: Session, email: str, password: str) -> User:
    user = User(name="Usuário Teste", email=email, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_login_with_valid_credentials_returns_tokens(client: TestClient, session: Session) -> None:
    """Login com email/senha corretos deve retornar access e refresh token."""
    _create_user(session, "teste@example.com", "senha-forte-123")

    response = client.post(
        "/auth/login", data={"username": "teste@example.com", "password": "senha-forte-123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_returns_401(client: TestClient, session: Session) -> None:
    """Login com senha errada deve retornar 401."""
    _create_user(session, "teste2@example.com", "senha-forte-123")

    response = client.post(
        "/auth/login", data={"username": "teste2@example.com", "password": "senha-errada"}
    )

    assert response.status_code == 401


def test_refresh_token_issues_new_access_token(client: TestClient, session: Session) -> None:
    """Um refresh token válido deve emitir um novo par de tokens."""
    _create_user(session, "teste3@example.com", "senha-forte-123")
    login_response = client.post(
        "/auth/login", data={"username": "teste3@example.com", "password": "senha-forte-123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_me_endpoint_requires_valid_token(client: TestClient, session: Session) -> None:
    """O endpoint /auth/me deve retornar os dados do usuário autenticado."""
    user = _create_user(session, "teste4@example.com", "senha-forte-123")
    login_response = client.post(
        "/auth/login", data={"username": "teste4@example.com", "password": "senha-forte-123"}
    )
    access_token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    assert response.json()["email"] == user.email