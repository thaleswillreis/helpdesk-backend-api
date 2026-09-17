"""Contratos de entrada/saída para abertura de chamado via catálogo de serviços."""

from pydantic import BaseModel, Field

from app.models.enums import PrioridadeChamado


class CatalogAnswerInput(BaseModel):
    """Uma resposta de campo, enviada ao abrir uma solicitação via catálogo."""

    field_id: int
    value: str


class TicketFromCatalogCreate(BaseModel):
    """Dados para abrir um chamado a partir de um item do catálogo de serviços."""

    catalog_item_id: int
    answers: list[CatalogAnswerInput] = Field(default_factory=list)
    priority: PrioridadeChamado | None = Field(
        default=None,
        description="Se omitido, usa a prioridade padrão da categoria do item.",
    )
    requester_id: int | None = Field(
        default=None,
        description="Solicitante do chamado. Se omitido, assume o usuário autenticado.",
    )


class TicketCatalogAnswerRead(BaseModel):
    """Uma resposta registrada, com o rótulo do campo para exibição."""

    field_id: int
    label: str
    value: str