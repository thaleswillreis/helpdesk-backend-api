"""Modelo de dados para respostas de formulário de uma solicitação via catálogo."""

from sqlmodel import Field, SQLModel


class TicketCatalogAnswer(SQLModel, table=True):
    """Resposta de um campo do formulário, vinculada a um chamado."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    field_id: int = Field(foreign_key="catalogitemfield.id")
    value: str