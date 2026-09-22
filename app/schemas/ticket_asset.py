"""Contratos de entrada/saída para o vínculo entre chamados e ativos do CMDB."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketAssetCreate(BaseModel):
    """Dados para vincular um ativo a um chamado."""

    asset_id: int


class TicketAssetRead(BaseModel):
    """Dados públicos de um vínculo entre chamado e ativo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    asset_id: int
    linked_by: int
    linked_at: datetime
