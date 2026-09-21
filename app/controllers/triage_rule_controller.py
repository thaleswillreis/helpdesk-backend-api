"""Endpoints de gestão de regras do motor de triagem automática."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.triage_rule import TriageRuleCreate, TriageRuleRead, TriageRuleUpdate
from app.services.triage_service import (
    CategoryNotFoundError,
    TeamNotFoundError,
    TriageRuleNotFoundError,
    create_rule,
    delete_rule,
    list_rules,
    update_rule,
)

router = APIRouter(prefix="/triage-rules", tags=["automation"])


@router.post("", response_model=TriageRuleRead, status_code=status.HTTP_201_CREATED)
def add_triage_rule(
    data: TriageRuleCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> TriageRuleRead:
    """Cria uma regra de triagem automática. Restrito a administradores."""
    try:
        rule = create_rule(session, data)
    except (CategoryNotFoundError, TeamNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TriageRuleRead.model_validate(rule)


@router.get("", response_model=list[TriageRuleRead])
def get_triage_rules(
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> list[TriageRuleRead]:
    """Lista as regras de triagem cadastradas. Restrito a admin/tecnico."""
    return [TriageRuleRead.model_validate(r) for r in list_rules(session)]


@router.patch("/{rule_id}", response_model=TriageRuleRead)
def edit_triage_rule(
    rule_id: int,
    data: TriageRuleUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> TriageRuleRead:
    """Atualiza uma regra de triagem. Restrito a administradores."""
    try:
        rule = update_rule(session, rule_id, data)
    except TriageRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (CategoryNotFoundError, TeamNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return TriageRuleRead.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_triage_rule(
    rule_id: int,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> None:
    """Remove uma regra de triagem. Restrito a administradores."""
    try:
        delete_rule(session, rule_id)
    except TriageRuleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc