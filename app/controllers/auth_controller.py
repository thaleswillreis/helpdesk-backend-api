"""Endpoints de autenticação."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import RefreshRequest, Token
from app.services.auth_service import (
    InvalidCredentialsError,
    InvalidTokenError,
    authenticate_user,
    issue_tokens,
    refresh_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    """Autentica o usuário (email/senha) e emite access + refresh token."""
    try:
        user = authenticate_user(session, form_data.username, form_data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)) -> Token:
    """Emite um novo par de tokens a partir de um refresh token válido."""
    try:
        return refresh_access_token(session, payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)) -> dict:
    """Endpoint de teste: retorna os dados básicos do usuário autenticado."""
    return {"id": current_user.id, "name": current_user.name, "email": current_user.email}