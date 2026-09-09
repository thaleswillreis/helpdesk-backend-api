"""Regras de negócio para políticas de SLA."""

from sqlmodel import Session, select

from app.models.sla_policy import SLAPolicy
from app.schemas.sla_policy import SLAPolicyCreate, SLAPolicyUpdate


class SLAPolicyNotFoundError(Exception):
    """Levantado quando a política de SLA informada não existe."""


class DuplicateSLAPolicyError(Exception):
    """Levantado ao tentar criar uma política para uma prioridade que já tem uma."""


def create_policy(session: Session, data: SLAPolicyCreate) -> SLAPolicy:
    """Cria a política de SLA para uma prioridade."""
    existing = session.exec(
        select(SLAPolicy).where(SLAPolicy.priority == data.priority)
    ).first()
    if existing is not None:
        raise DuplicateSLAPolicyError(
            f"Já existe uma política de SLA para a prioridade '{data.priority.value}'."
        )

    policy = SLAPolicy(
        priority=data.priority,
        response_time_minutes=data.response_time_minutes,
        resolution_time_minutes=data.resolution_time_minutes,
    )
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy


def list_policies(session: Session) -> list[SLAPolicy]:
    """Lista todas as políticas de SLA cadastradas."""
    return list(session.exec(select(SLAPolicy)))


def update_policy(session: Session, policy_id: int, data: SLAPolicyUpdate) -> SLAPolicy:
    """Atualiza os prazos de uma política de SLA existente."""
    policy = session.get(SLAPolicy, policy_id)
    if policy is None:
        raise SLAPolicyNotFoundError("Política de SLA não encontrada.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy