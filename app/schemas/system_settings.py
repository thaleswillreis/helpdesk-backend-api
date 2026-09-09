"""Contratos de entrada/saída para configurações globais do sistema."""

from pydantic import BaseModel, ConfigDict, Field


class SystemSettingsUpdate(BaseModel):
    """Campos que podem ser atualizados nas configurações globais."""

    sla_at_risk_threshold_percent: int | None = Field(default=None, ge=1, le=99)


class SystemSettingsRead(BaseModel):
    """Configurações globais atuais do sistema."""

    model_config = ConfigDict(from_attributes=True)

    sla_at_risk_threshold_percent: int