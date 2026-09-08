"""Contratos de entrada/saída para comentários de chamados."""

from datetime import datetime

from pydantic import BaseModel, Field


class TicketCommentCreate(BaseModel):
    """Dados para adicionar um comentário a um chamado."""

    content: str = Field(min_length=1)
    is_internal: bool = Field(
        default=False, description="Se True, o comentário só é visível para admin/tecnico."
    )
    mentioned_user_ids: list[int] = Field(default_factory=list)


class TicketCommentRead(BaseModel):
    """Dados públicos de um comentário, incluindo os usuários mencionados."""

    id: int
    ticket_id: int
    author_id: int
    content: str
    is_internal: bool
    created_at: datetime
    mentioned_user_ids: list[int] = Field(default_factory=list)