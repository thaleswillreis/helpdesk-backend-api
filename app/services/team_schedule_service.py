"""Regras de negócio para o expediente (horário de funcionamento) de equipes."""

from sqlmodel import Session, select

from app.models.team import Team
from app.models.team_schedule import TeamSchedule
from app.schemas.team_schedule import TeamScheduleCreate


class TeamNotFoundError(Exception):
    """Levantado quando a equipe informada não existe."""


class DuplicateScheduleDayError(Exception):
    """Levantado ao tentar cadastrar duas janelas para o mesmo dia da semana."""


class ScheduleNotFoundError(Exception):
    """Levantado quando a janela de expediente informada não existe."""


def add_schedule_entry(session: Session, team_id: int, data: TeamScheduleCreate) -> TeamSchedule:
    """Cadastra a janela de expediente de um dia da semana para a equipe."""
    if session.get(Team, team_id) is None:
        raise TeamNotFoundError("Equipe não encontrada.")

    existing = session.exec(
        select(TeamSchedule).where(
            TeamSchedule.team_id == team_id, TeamSchedule.weekday == data.weekday
        )
    ).first()
    if existing is not None:
        raise DuplicateScheduleDayError(
            f"Já existe uma janela de expediente cadastrada para o dia {data.weekday} desta equipe."
        )

    entry = TeamSchedule(
        team_id=team_id,
        weekday=data.weekday,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def list_schedule(session: Session, team_id: int) -> list[TeamSchedule]:
    """Lista o expediente completo de uma equipe (vazio = 24/7)."""
    if session.get(Team, team_id) is None:
        raise TeamNotFoundError("Equipe não encontrada.")

    query = select(TeamSchedule).where(TeamSchedule.team_id == team_id)
    return list(session.exec(query))


def remove_schedule_entry(session: Session, team_id: int, schedule_id: int) -> None:
    """Remove uma janela de expediente da equipe."""
    entry = session.get(TeamSchedule, schedule_id)
    if entry is None or entry.team_id != team_id:
        raise ScheduleNotFoundError("Janela de expediente não encontrada para esta equipe.")

    session.delete(entry)
    session.commit()