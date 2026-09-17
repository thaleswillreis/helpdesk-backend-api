"""Regras de negócio para o catálogo de serviços."""

from sqlmodel import Session, select

from app.core.roles import is_staff
from app.models.catalog_item_field import CatalogItemField
from app.models.category import Category
from app.models.service_catalog_item import ServiceCatalogItem
from app.models.subcategory import Subcategory
from app.models.user import User
from app.schemas.catalog_item_field import CatalogItemFieldCreate, CatalogItemFieldUpdate
from app.schemas.service_catalog_item import ServiceCatalogItemCreate, ServiceCatalogItemUpdate


class ServiceCatalogItemNotFoundError(Exception):
    """Levantado quando o item de catálogo informado não existe ou não é visível."""


class CategoryNotFoundError(Exception):
    """Levantado quando a categoria informada não existe."""


class SubcategoryMismatchError(Exception):
    """Levantado quando a subcategoria informada não pertence à categoria informada."""

class CatalogItemFieldNotFoundError(Exception):
    """Levantado quando o campo de formulário informado não existe neste item."""


def _validate_category(session: Session, category_id: int, subcategory_id: int | None) -> None:
    category = session.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError("Categoria informada não encontrada.")

    if subcategory_id is not None:
        subcategory = session.get(Subcategory, subcategory_id)
        if subcategory is None:
            raise CategoryNotFoundError("Subcategoria informada não encontrada.")
        if subcategory.category_id != category_id:
            raise SubcategoryMismatchError(
                "A subcategoria informada não pertence à categoria informada."
            )


def create_item(session: Session, data: ServiceCatalogItemCreate) -> ServiceCatalogItem:
    """Cria um item do catálogo de serviços."""
    _validate_category(session, data.category_id, data.subcategory_id)

    item = ServiceCatalogItem(
        name=data.name,
        description=data.description,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        requires_approval=data.requires_approval,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_items(
    session: Session, current_user: User, category_id: int | None = None
) -> list[ServiceCatalogItem]:
    """Lista itens do catálogo: staff vê tudo; solicitante só vê itens ativos."""
    query = select(ServiceCatalogItem)
    if not is_staff(current_user):
        query = query.where(ServiceCatalogItem.is_active.is_(True))
    if category_id is not None:
        query = query.where(ServiceCatalogItem.category_id == category_id)

    return list(session.exec(query))


def get_item(session: Session, item_id: int, current_user: User) -> ServiceCatalogItem:
    """Busca um item por id, respeitando a visibilidade por status ativo/inativo."""
    item = session.get(ServiceCatalogItem, item_id)
    if item is None:
        raise ServiceCatalogItemNotFoundError("Item de catálogo não encontrado.")

    if not is_staff(current_user) and not item.is_active:
        raise ServiceCatalogItemNotFoundError("Item de catálogo não encontrado.")

    return item


def update_item(
    session: Session, item_id: int, data: ServiceCatalogItemUpdate
) -> ServiceCatalogItem:
    """Atualiza um item do catálogo. O controller já restringe isso a admin."""
    item = session.get(ServiceCatalogItem, item_id)
    if item is None:
        raise ServiceCatalogItemNotFoundError("Item de catálogo não encontrado.")

    final_category_id = data.category_id if data.category_id is not None else item.category_id
    final_subcategory_id = (
        data.subcategory_id if data.subcategory_id is not None else item.subcategory_id
    )
    if data.category_id is not None or data.subcategory_id is not None:
        _validate_category(session, final_category_id, final_subcategory_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def add_field(
    session: Session, catalog_item_id: int, data: CatalogItemFieldCreate
) -> CatalogItemField:
    """Adiciona um campo de formulário a um item do catálogo."""
    if session.get(ServiceCatalogItem, catalog_item_id) is None:
        raise ServiceCatalogItemNotFoundError("Item de catálogo não encontrado.")

    field = CatalogItemField(
        catalog_item_id=catalog_item_id,
        label=data.label,
        field_type=data.field_type,
        is_required=data.is_required,
        options=data.options,
        display_order=data.display_order,
    )
    session.add(field)
    session.commit()
    session.refresh(field)
    return field


def list_fields(session: Session, catalog_item_id: int) -> list[CatalogItemField]:
    """Lista os campos de formulário de um item, ordenados por display_order."""
    if session.get(ServiceCatalogItem, catalog_item_id) is None:
        raise ServiceCatalogItemNotFoundError("Item de catálogo não encontrado.")

    query = (
        select(CatalogItemField)
        .where(CatalogItemField.catalog_item_id == catalog_item_id)
        .order_by(CatalogItemField.display_order)
    )
    return list(session.exec(query))


def update_field(
    session: Session, catalog_item_id: int, field_id: int, data: CatalogItemFieldUpdate
) -> CatalogItemField:
    """Atualiza um campo de formulário existente."""
    field = session.get(CatalogItemField, field_id)
    if field is None or field.catalog_item_id != catalog_item_id:
        raise CatalogItemFieldNotFoundError("Campo não encontrado para este item de catálogo.")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(field, key, value)

    session.add(field)
    session.commit()
    session.refresh(field)
    return field


def remove_field(session: Session, catalog_item_id: int, field_id: int) -> None:
    """Remove um campo de formulário de um item do catálogo."""
    field = session.get(CatalogItemField, field_id)
    if field is None or field.catalog_item_id != catalog_item_id:
        raise CatalogItemFieldNotFoundError("Campo não encontrado para este item de catálogo.")

    session.delete(field)
    session.commit()