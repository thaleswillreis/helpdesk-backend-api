"""Contratos de entrada/saída para políticas de SLA."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PrioridadeChamado


class SLAPolicyCreate(BaseModel):
    """Dados para criar uma política de SLA para uma prioridade."""

    priority: PrioridadeChamado
    response_time_minutes: int = Field(gt=0)
    resolution_time_minutes: int = Field(gt=0)


class SLAPolicyUpdate(BaseModel):
    """Campos que podem ser atualizados em uma política de SLA."""

    response_time_minutes: int | None = Field(default=None, gt=0)
    resolution_time_minutes: int | None = Field(default=None, gt=0)


class SLAPolicyRead(BaseModel):
    """Dados públicos de uma política de SLA."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    priority: PrioridadeChamado
    response_time_minutes: int
    resolution_time_minutes: int