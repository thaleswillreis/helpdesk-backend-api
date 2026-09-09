"""Modelo de dados para configurações globais do sistema (linha única)."""

from sqlmodel import Field, SQLModel


class SystemSettings(SQLModel, table=True):
    """Configurações globais da aplicação. Sempre uma única linha (id=1)."""

    id: int = Field(default=1, primary_key=True)
    sla_at_risk_threshold_percent: int = Field(
        default=80,
        ge=1,
        le=99,
        description="A partir de quantos % do prazo consumido um chamado é sinalizado 'em risco'.",
    )