"""Regras de negócio de autenticação."""

import jwt
from sqlmodel import Session, select

from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import Token


class InvalidCredentialsError(Exception):
    """Levantado quando email/senha não conferem ou o usuário está inativo."""


class InvalidTokenError(Exception):
    """Levantado quando um token é inválido, expirado ou do tipo errado."""


def authenticate_user(session: Session, email: str, password: str) -> User:
    """Valida as credenciais e retorna o usuário autenticado."""
    user = session.exec(select(User).where(User.email == email)).first()

    if user is None or not user.is_active or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Email ou senha inválidos.")

    return user


def issue_tokens(user: User) -> Token:
    """Emite o par access/refresh token para um usuário já autenticado."""
    subject = str(user.id)
    return Token(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def refresh_access_token(session: Session, refresh_token: str) -> Token:
    """Valida um refresh token e emite um novo par de tokens."""
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Refresh token inválido ou expirado.") from exc

    if payload.get("type") != TokenType.REFRESH.value:
        raise InvalidTokenError("Token informado não é um refresh token.")

    user = session.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise InvalidTokenError("Usuário não encontrado ou inativo.")

    return issue_tokens(user)