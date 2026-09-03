"""Endpoints de gestão de usuários."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import (
    EmailAlreadyExistsError,
    RoleNotFoundError,
    create_user,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> UserRead:
    """Cria um novo usuário. Restrito a administradores."""
    try:
        user = create_user(session, data)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role_name=user.role.name if user.role else None,
        is_active=user.is_active,
    )