"""Endpoints de gestão de equipes e seus membros."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.schemas.team import (
    TeamCreate,
    TeamMemberAdd,
    TeamMemberRead,
    TeamRead,
    TeamUpdate,
)
from app.services.team_service import (
    DuplicateTeamNameError,
    InvalidTeamMemberError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    TeamNotFoundError,
    add_member,
    create_team,
    list_members,
    list_teams,
    remove_member,
    update_team,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def add_team(
    data: TeamCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> TeamRead:
    """Cria uma nova equipe. Restrito a administradores."""
    try:
        team = create_team(session, data)
    except DuplicateTeamNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return TeamRead.model_validate(team)


@router.get("", response_model=list[TeamRead])
def get_teams(
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> list[TeamRead]:
    """Lista todas as equipes. Qualquer usuário autenticado pode consultar."""
    return [TeamRead.model_validate(team) for team in list_teams(session)]


@router.patch("/{team_id}", response_model=TeamRead)
def edit_team(
    team_id: int,
    data: TeamUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> TeamRead:
    """Atualiza uma equipe existente. Restrito a administradores."""
    try:
        team = update_team(session, team_id, data)
    except TeamNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return TeamRead.model_validate(team)


@router.post("/{team_id}/members", status_code=status.HTTP_204_NO_CONTENT)
def add_team_member(
    team_id: int,
    data: TeamMemberAdd,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> None:
    """Adiciona um técnico a uma equipe. Restrito a administradores."""
    try:
        add_member(session, team_id, data.user_id)
    except TeamNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidTeamMemberError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except MembershipAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> None:
    """Remove um técnico de uma equipe. Restrito a administradores."""
    try:
        remove_member(session, team_id, user_id)
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{team_id}/members", response_model=list[TeamMemberRead])
def get_team_members(
    team_id: int,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> list[TeamMemberRead]:
    """Lista os técnicos membros de uma equipe."""
    try:
        members = list_members(session, team_id)
    except TeamNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return [TeamMemberRead.model_validate(member) for member in members]