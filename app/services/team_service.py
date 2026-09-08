"""Regras de negócio para equipes e seus membros."""

from sqlmodel import Session, select

from app.models.team import Team
from app.models.team_membership import TeamMembership
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate


class TeamNotFoundError(Exception):
    """Levantado quando a equipe informada não existe."""


class DuplicateTeamNameError(Exception):
    """Levantado ao tentar criar/renomear equipe para um nome já usado."""


class InvalidTeamMemberError(Exception):
    """Levantado quando o usuário informado não existe, está inativo, ou não é técnico."""


class MembershipAlreadyExistsError(Exception):
    """Levantado ao tentar adicionar um técnico que já é membro da equipe."""


class MembershipNotFoundError(Exception):
    """Levantado ao tentar remover um vínculo que não existe."""


def create_team(session: Session, data: TeamCreate) -> Team:
    """Cria uma nova equipe."""
    existing = session.exec(select(Team).where(Team.name == data.name)).first()
    if existing is not None:
        raise DuplicateTeamNameError(f"Já existe uma equipe chamada '{data.name}'.")

    team = Team(name=data.name, description=data.description)
    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def list_teams(session: Session) -> list[Team]:
    """Lista todas as equipes."""
    return list(session.exec(select(Team)))


def update_team(session: Session, team_id: int, data: TeamUpdate) -> Team:
    """Atualiza uma equipe existente."""
    team = session.get(Team, team_id)
    if team is None:
        raise TeamNotFoundError("Equipe não encontrada.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    session.add(team)
    session.commit()
    session.refresh(team)
    return team


def add_member(session: Session, team_id: int, user_id: int) -> None:
    """Adiciona um técnico a uma equipe."""
    team = session.get(Team, team_id)
    if team is None:
        raise TeamNotFoundError("Equipe não encontrada.")

    user = session.get(User, user_id)
    if user is None or not user.is_active or user.role is None or user.role.name != "tecnico":
        raise InvalidTeamMemberError(
            "Usuário informado não encontrado, inativo, ou não possui papel de técnico."
        )

    existing = session.get(TeamMembership, (team_id, user_id))
    if existing is not None:
        raise MembershipAlreadyExistsError("Este técnico já é membro desta equipe.")

    session.add(TeamMembership(team_id=team_id, user_id=user_id))
    session.commit()


def remove_member(session: Session, team_id: int, user_id: int) -> None:
    """Remove um técnico de uma equipe."""
    membership = session.get(TeamMembership, (team_id, user_id))
    if membership is None:
        raise MembershipNotFoundError("Este técnico não é membro desta equipe.")

    session.delete(membership)
    session.commit()


def list_members(session: Session, team_id: int) -> list[User]:
    """Lista os técnicos membros de uma equipe."""
    if session.get(Team, team_id) is None:
        raise TeamNotFoundError("Equipe não encontrada.")

    query = (
        select(User)
        .join(TeamMembership, TeamMembership.user_id == User.id)
        .where(TeamMembership.team_id == team_id)
    )
    return list(session.exec(query))