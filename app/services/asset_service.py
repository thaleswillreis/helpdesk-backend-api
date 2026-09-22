"""Regras de negócio para ativos do CMDB e seus relacionamentos."""

from sqlmodel import Session, select

from app.models.asset import Asset
from app.models.asset_relationship import AssetRelationship
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate
from app.schemas.asset_relationship import AssetRelationshipCreate


class AssetNotFoundError(Exception):
    """Levantado quando o ativo informado não existe."""


class DuplicateSerialNumberError(Exception):
    """Levantado ao tentar cadastrar um número de série já usado por outro ativo."""


class InvalidResponsibleError(Exception):
    """Levantado quando o usuário responsável informado não existe ou está inativo."""


class DuplicateRelationshipError(Exception):
    """Levantado ao tentar criar um relacionamento idêntico a um já existente."""


class RelationshipNotFoundError(Exception):
    """Levantado quando o relacionamento informado não existe."""


def _validate_responsible(session: Session, assigned_to: int | None) -> None:
    if assigned_to is None:
        return
    user = session.get(User, assigned_to)
    if user is None or not user.is_active:
        raise InvalidResponsibleError(
            "Usuário responsável informado não encontrado ou inativo."
        )


def create_asset(session: Session, data: AssetCreate) -> Asset:
    """Cadastra um novo ativo."""
    if data.serial_number is not None:
        existing = session.exec(
            select(Asset).where(Asset.serial_number == data.serial_number)
        ).first()
        if existing is not None:
            raise DuplicateSerialNumberError(
                f"Já existe um ativo com o número de série '{data.serial_number}'."
            )

    _validate_responsible(session, data.assigned_to)

    asset = Asset(**data.model_dump())
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def list_assets(
    session: Session, asset_type: str | None = None, status: str | None = None
) -> list[Asset]:
    """Lista ativos, opcionalmente filtrando por tipo e/ou status."""
    query = select(Asset)
    if asset_type is not None:
        query = query.where(Asset.asset_type == asset_type)
    if status is not None:
        query = query.where(Asset.status == status)
    return list(session.exec(query))


def get_asset(session: Session, asset_id: int) -> Asset:
    """Busca um ativo por id."""
    asset = session.get(Asset, asset_id)
    if asset is None:
        raise AssetNotFoundError("Ativo não encontrado.")
    return asset


def update_asset(session: Session, asset_id: int, data: AssetUpdate) -> Asset:
    """Atualiza um ativo existente."""
    asset = session.get(Asset, asset_id)
    if asset is None:
        raise AssetNotFoundError("Ativo não encontrado.")

    update_data = data.model_dump(exclude_unset=True)

    if "serial_number" in update_data and update_data["serial_number"] is not None:
        existing = session.exec(
            select(Asset).where(
                Asset.serial_number == update_data["serial_number"],
                Asset.id != asset_id,
            )
        ).first()
        if existing is not None:
            raise DuplicateSerialNumberError(
                f"Já existe um ativo com o número de série '{update_data['serial_number']}'."
            )

    if "assigned_to" in update_data:
        _validate_responsible(session, update_data["assigned_to"])

    for field, value in update_data.items():
        setattr(asset, field, value)

    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def create_relationship(
    session: Session, data: AssetRelationshipCreate
) -> AssetRelationship:
    """Cria um relacionamento de dependência entre dois ativos."""
    if session.get(Asset, data.from_asset_id) is None:
        raise AssetNotFoundError("Ativo de origem não encontrado.")
    if session.get(Asset, data.to_asset_id) is None:
        raise AssetNotFoundError("Ativo de destino não encontrado.")

    existing = session.exec(
        select(AssetRelationship).where(
            AssetRelationship.from_asset_id == data.from_asset_id,
            AssetRelationship.to_asset_id == data.to_asset_id,
            AssetRelationship.relationship_type == data.relationship_type,
        )
    ).first()
    if existing is not None:
        raise DuplicateRelationshipError(
            "Este relacionamento já existe entre os dois ativos."
        )

    relationship = AssetRelationship(**data.model_dump())
    session.add(relationship)
    session.commit()
    session.refresh(relationship)
    return relationship


def list_relationships(session: Session, asset_id: int) -> list[AssetRelationship]:
    """Lista os relacionamentos de um ativo, tanto como origem quanto como destino."""
    if session.get(Asset, asset_id) is None:
        raise AssetNotFoundError("Ativo não encontrado.")

    query = select(AssetRelationship).where(
        (AssetRelationship.from_asset_id == asset_id)
        | (AssetRelationship.to_asset_id == asset_id)
    )
    return list(session.exec(query))


def delete_relationship(session: Session, relationship_id: int) -> None:
    """Remove um relacionamento entre ativos."""
    relationship = session.get(AssetRelationship, relationship_id)
    if relationship is None:
        raise RelationshipNotFoundError("Relacionamento não encontrado.")

    session.delete(relationship)
    session.commit()
