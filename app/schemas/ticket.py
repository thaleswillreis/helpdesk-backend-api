"""Contratos de entrada/saída para chamados (tickets)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PrioridadeChamado, StatusChamado


class TicketCreate(BaseModel):
    """Dados necessários para abrir um novo chamado."""

    title: str = Field(max_length=200)
    description: str
    category_id: int
    subcategory_id: int | None = None
    priority: PrioridadeChamado | None = Field(
        default=None,
        description="Se omitido, usa a prioridade padrão da categoria "
        "(ou 'vip', automaticamente, se o solicitante for VIP).",
    )
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
    category_id: int | None = None
    subcategory_id: int | None = None
    assigned_to: int | None = None
    team_id: int | None = None
    comment: str | None = Field(
        default=None,
        description="Observação opcional, registrada junto com as mudanças no histórico.",
    )


class TicketRead(BaseModel):
    """Dados públicos de um chamado, retornados pela API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: StatusChamado
    priority: PrioridadeChamado
    category_id: int
    subcategory_id: int | None
    requester_id: int
    assigned_to: int | None
    team_id: int | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None