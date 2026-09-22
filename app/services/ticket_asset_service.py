"""Regras de negócio para o vínculo entre chamados e ativos do CMDB, e sugestão de impacto.

Decisão de arquitetura: seguindo o padrão de mercado (ServiceNow "Impact
Analysis", Jira Service Management, Freshservice), o vínculo chamado-ativo é
sempre manual — o sistema nunca associa um ativo a um chamado por conta
própria. A navegação pelo grafo de AssetRelationship (função
suggest_affected_assets) é puramente informativa: sugere candidatos a partir
dos ativos já vinculados diretamente, mas a decisão de vincular continua
sendo do técnico.
"""

from sqlmodel import Session, select

from app.models.asset import Asset
from app.models.asset_relationship import AssetRelationship
from app.models.ticket import Ticket
from app.models.ticket_asset import TicketAsset
from app.models.user import User
from app.schemas.ticket_asset import TicketAssetCreate


class TicketNotFoundError(Exception):
    """Levantado quando o chamado informado não existe."""


class AssetNotFoundError(Exception):
    """Levantado quando o ativo informado não existe."""


class DuplicateLinkError(Exception):
    """Levantado ao tentar vincular um ativo já vinculado ao mesmo chamado."""


class LinkNotFoundError(Exception):
    """Levantado quando o vínculo entre chamado e ativo não existe."""


def link_asset(
    session: Session, ticket_id: int, data: TicketAssetCreate, current_user: User
) -> TicketAsset:
    """Vincula manualmente um ativo a um chamado."""
    if session.get(Ticket, ticket_id) is None:
        raise TicketNotFoundError("Chamado não encontrado.")
    if session.get(Asset, data.asset_id) is None:
        raise AssetNotFoundError("Ativo não encontrado.")

    existing = session.exec(
        select(TicketAsset).where(
            TicketAsset.ticket_id == ticket_id, TicketAsset.asset_id == data.asset_id
        )
    ).first()
    if existing is not None:
        raise DuplicateLinkError("Este ativo já está vinculado a este chamado.")

    link = TicketAsset(
        ticket_id=ticket_id, asset_id=data.asset_id, linked_by=current_user.id
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def list_linked_assets(session: Session, ticket_id: int) -> list[TicketAsset]:
    """Lista os ativos vinculados a um chamado."""
    if session.get(Ticket, ticket_id) is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    query = select(TicketAsset).where(TicketAsset.ticket_id == ticket_id)
    return list(session.exec(query))


def unlink_asset(session: Session, ticket_id: int, asset_id: int) -> None:
    """Remove o vínculo entre um chamado e um ativo."""
    link = session.exec(
        select(TicketAsset).where(
            TicketAsset.ticket_id == ticket_id, TicketAsset.asset_id == asset_id
        )
    ).first()
    if link is None:
        raise LinkNotFoundError("Vínculo entre chamado e ativo não encontrado.")

    session.delete(link)
    session.commit()


def suggest_affected_assets(session: Session, ticket_id: int) -> list[Asset]:
    """Sugere ativos potencialmente afetados, navegando um salto no grafo de
    AssetRelationship a partir dos ativos já vinculados diretamente ao chamado.

    Puramente informativo — nunca vincula nada automaticamente.
    """
    if session.get(Ticket, ticket_id) is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    linked = list(
        session.exec(
            select(TicketAsset.asset_id).where(TicketAsset.ticket_id == ticket_id)
        )
    )
    if not linked:
        return []

    linked_ids = set(linked)

    relationships = session.exec(
        select(AssetRelationship).where(
            AssetRelationship.from_asset_id.in_(linked_ids)
            | AssetRelationship.to_asset_id.in_(linked_ids)
        )
    )

    candidate_ids: set[int] = set()
    for rel in relationships:
        if rel.from_asset_id in linked_ids:
            candidate_ids.add(rel.to_asset_id)
        if rel.to_asset_id in linked_ids:
            candidate_ids.add(rel.from_asset_id)

    candidate_ids -= linked_ids
    if not candidate_ids:
        return []

    return list(session.exec(select(Asset).where(Asset.id.in_(candidate_ids))))
