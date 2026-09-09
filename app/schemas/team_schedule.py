"""Contratos de entrada/saída para o expediente de uma equipe."""

from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class TeamScheduleCreate(BaseModel):
    """Dados para cadastrar a janela de expediente de um dia da semana."""

    weekday: int = Field(ge=0, le=6, description="0=segunda, ..., 6=domingo")
    start_time: time
    end_time: time = Field(
        description="Se <= start_time, o turno cruza a meia-noite (ex.: 18h às 6h)."
    )


class TeamScheduleRead(BaseModel):
    """Dados públicos de uma janela de expediente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    weekday: int
    start_time: time
    end_time: time