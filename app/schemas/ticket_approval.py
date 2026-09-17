"""Contratos de entrada para decisão de aprovação de um chamado."""

from pydantic import BaseModel


class TicketApprovalDecision(BaseModel):
    """Decisão de aprovar ou rejeitar um chamado aguardando aprovação."""

    approved: bool
    comment: str | None = None