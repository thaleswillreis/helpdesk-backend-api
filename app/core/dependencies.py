"""Dependências reutilizáveis de autenticação e autorização para os endpoints."""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import TokenType, decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    """Resolve o usuário autenticado a partir do access token enviado."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise credentials_error from exc

    if payload.get("type") != TokenType.ACCESS.value:
        raise credentials_error

    user = session.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise credentials_error

    return user


def require_role(*allowed_roles: str):
    """Fábrica de dependency que restringe o endpoint aos papéis informados."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name if current_user.role else None
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este recurso.",
            )
        return current_user

    return checker