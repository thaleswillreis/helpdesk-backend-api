"""Endpoints de gestão de políticas de SLA."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.sla_policy import SLAPolicyCreate, SLAPolicyRead, SLAPolicyUpdate
from app.services.sla_policy_service import (
    DuplicateSLAPolicyError,
    SLAPolicyNotFoundError,
    create_policy,
    list_policies,
    update_policy,
)

router = APIRouter(prefix="/sla-policies", tags=["sla"])


@router.post("", response_model=SLAPolicyRead, status_code=status.HTTP_201_CREATED)
def add_policy(
    data: SLAPolicyCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> SLAPolicyRead:
    """Cria a política de SLA para uma prioridade. Restrito a administradores."""
    try:
        policy = create_policy(session, data)
    except DuplicateSLAPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return SLAPolicyRead.model_validate(policy)


@router.get("", response_model=list[SLAPolicyRead])
def get_policies(
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> list[SLAPolicyRead]:
    """Lista as políticas de SLA cadastradas. Restrito a admin/tecnico."""
    return [SLAPolicyRead.model_validate(p) for p in list_policies(session)]


@router.patch("/{policy_id}", response_model=SLAPolicyRead)
def edit_policy(
    policy_id: int,
    data: SLAPolicyUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> SLAPolicyRead:
    """Atualiza os prazos de uma política de SLA. Restrito a administradores."""
    try:
        policy = update_policy(session, policy_id, data)
    except SLAPolicyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SLAPolicyRead.model_validate(policy)