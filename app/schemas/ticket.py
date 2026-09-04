"""Contratos de entrada/saída para chamados (tickets)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PrioridadeChamado, StatusChamado


class TicketCreate(BaseModel):
    """Dados necessários para abrir um novo chamado."""

    title: str = Field(max_length=200)
    description: str
    priority: PrioridadeChamado
    category: str = Field(max_length=100)
    requester_id: int | None = Field(
        default=None,
        description="Solicitante do chamado. Se omitido, assume o usuário autenticado. "
        "Só admin/tecnico pode informar um solicitante diferente de si mesmo.",
    )


class TicketUpdate(BaseModel):
    """Campos que podem ser atualizados em um chamado existente. Restrito a admin/tecnico."""

    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    status: StatusChamado | None = None
    priority: PrioridadeChamado | None = None
    category: str | None = Field(default=None, max_length=100)
    assigned_to: int | None = None


class TicketRead(BaseModel):
    """Dados públicos de um chamado, retornados pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: StatusChamado
    priority: PrioridadeChamado
    category: str
    requester_id: int
    assigned_to: int | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None