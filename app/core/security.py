"""Funções de segurança: hashing de senha (Argon2) e emissão/validação de JWT."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_password_hasher = PasswordHasher()


class TokenType(StrEnum):
    """Tipos de token JWT emitidos pela API."""

    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    """Gera o hash Argon2 de uma senha em texto plano."""
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    try:
        return _password_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload = {"sub": subject, "type": token_type.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    """Cria um access token de curta duração para o usuário informado."""
    return _create_token(
        subject, TokenType.ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(subject: str) -> str:
    """Cria um refresh token de longa duração para o usuário informado."""
    return _create_token(
        subject, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str) -> dict:
    """Decodifica e valida um JWT, levantando jwt.PyJWTError se inválido/expirado."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])