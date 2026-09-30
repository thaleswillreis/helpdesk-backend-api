"""Modelo de dados para políticas de SLA por prioridade."""

from sqlmodel import Field, SQLModel

from app.models.enums import PrioridadeChamado, pg_enum_column


class SLAPolicy(SQLModel, table=True):
    """Prazos de resposta e solução esperados para uma prioridade de chamado."""

    id: int | None = Field(default=None, primary_key=True)
    priority: PrioridadeChamado = Field(
        sa_column=pg_enum_column(
            PrioridadeChamado, "prioridadechamado", unique=True, index=True
        ),
    )
    response_time_minutes: int = Field(gt=0)
    resolution_time_minutes: int = Field(gt=0)
