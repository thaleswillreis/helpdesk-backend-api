"""Contratos de saída para a listagem de monitoramento de chamados."""

from pydantic import BaseModel

from app.schemas.sla_status import SLAClockRead
from app.schemas.ticket import TicketRead


class TicketOverviewItem(TicketRead):
    """Um chamado na listagem de monitoramento, com o resumo do SLA já calculado."""

    sla_applicable: bool
    sla_response: SLAClockRead | None = None
    sla_resolution: SLAClockRead | None = None


class TicketOverviewPage(BaseModel):
    """Página de resultados da listagem de monitoramento."""

    total: int
    skip: int
    limit: int
    items: list[TicketOverviewItem]