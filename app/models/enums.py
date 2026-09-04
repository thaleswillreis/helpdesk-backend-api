"""Enums compartilhados do domínio de chamados (status e prioridade)."""

from enum import StrEnum


class StatusChamado(StrEnum):
    """Ciclo de vida de um chamado."""

    ABERTO = "aberto"
    EM_ATENDIMENTO = "em_atendimento"
    AGUARDANDO_SOLICITANTE = "aguardando_solicitante"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"
    CANCELADO = "cancelado"


# Chamado não recebe mais atualizações a partir daqui.
STATUS_ENCERRADOS = {StatusChamado.FECHADO, StatusChamado.CANCELADO}

# Usado no cálculo de SLA (Fase 4): CANCELADO não conta, pois não foi
# um atendimento real (ex.: usuário resolveu sozinho).
STATUS_QUE_CONTAM_SLA = {
    StatusChamado.ABERTO,
    StatusChamado.EM_ATENDIMENTO,
    StatusChamado.AGUARDANDO_SOLICITANTE,
    StatusChamado.RESOLVIDO,
    StatusChamado.FECHADO,
}


class PrioridadeChamado(StrEnum):
    """Nível de prioridade de um chamado."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"
    VIP = "vip"  # SLA equivalente a CRITICA; serve como alerta/destaque para os técnicos.


# Peso para ordenação de fila (Fase 3) — quanto maior, mais prioritário.
PESO_PRIORIDADE: dict[PrioridadeChamado, int] = {
    PrioridadeChamado.BAIXA: 1,
    PrioridadeChamado.MEDIA: 2,
    PrioridadeChamado.ALTA: 3,
    PrioridadeChamado.CRITICA: 4,
    PrioridadeChamado.VIP: 5,
}