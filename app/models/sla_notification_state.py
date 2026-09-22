"""Modelo de dados para rastrear o último status de SLA notificado de cada chamado.

Existe apenas para evitar notificações repetidas: sem isso, um chamado que
permanece 'at_risk' por várias execuções da verificação periódica geraria um
webhook a cada execução, em vez de um único alerta na transição de estado.
"""

from sqlmodel import Field, SQLModel


class SlaNotificationState(SQLModel, table=True):
    """Última situação de SLA observada para cada relógio de um chamado."""

    ticket_id: int = Field(foreign_key="ticket.id", primary_key=True)
    response_last_status: str | None = Field(default=None)
    resolution_last_status: str | None = Field(default=None)
