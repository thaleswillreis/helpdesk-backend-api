"""Modelo de dados para o expediente (horário de funcionamento) de uma equipe."""

from datetime import time

from sqlmodel import Field, SQLModel


class TeamSchedule(SQLModel, table=True):
    """Janela de expediente de uma equipe em um dia da semana.

    Uma equipe sem nenhuma linha cadastrada é considerada 24/7 (sem pausa de SLA).
    """

    id: int | None = Field(default=None, primary_key=True)
    team_id: int = Field(foreign_key="team.id", index=True)
    weekday: int = Field(ge=0, le=6, description="0=segunda, 1=terça, ..., 6=domingo")
    start_time: time
    end_time: time = Field(
        description="Se <= start_time, o turno cruza a meia-noite (ex.: 18h às 6h)."
    )