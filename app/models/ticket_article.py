"""Modelo de dados para o vínculo entre chamados e artigos da base de conhecimento."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class TicketArticle(SQLModel, table=True):
    """Vínculo de um artigo a um chamado (referência geral ou marcado como solução)."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    article_id: int = Field(foreign_key="article.id", index=True)

    is_resolution: bool = Field(default=False)

    linked_by: int = Field(foreign_key="user.id")
    linked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))