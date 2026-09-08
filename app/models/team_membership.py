"""Modelo de dados para o vínculo N:N entre equipes e técnicos."""

from sqlmodel import Field, SQLModel


class TeamMembership(SQLModel, table=True):
    """Vínculo de um técnico a uma equipe. Um técnico pode estar em várias equipes."""

    team_id: int = Field(foreign_key="team.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)