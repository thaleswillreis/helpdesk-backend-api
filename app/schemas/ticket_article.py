"""Contratos de entrada/saída para o vínculo entre chamados e artigos."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketArticleCreate(BaseModel):
    """Dados para vincular um artigo a um chamado."""

    article_id: int


class TicketArticleUpdate(BaseModel):
    """Dados para marcar/desmarcar um vínculo como a solução do chamado."""

    is_resolution: bool = Field(description="True marca este artigo como a solução do chamado.")


class TicketArticleRead(BaseModel):
    """Dados públicos de um vínculo entre chamado e artigo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    article_id: int
    is_resolution: bool
    linked_by: int
    linked_at: datetime