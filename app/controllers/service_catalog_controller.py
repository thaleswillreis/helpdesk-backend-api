"""Endpoints de gestão do catálogo de serviços."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.catalog_item_field import (
    CatalogItemFieldCreate,
    CatalogItemFieldRead,
    CatalogItemFieldUpdate,
)
from app.schemas.service_catalog_item import (
    ServiceCatalogItemCreate,
    ServiceCatalogItemRead,
    ServiceCatalogItemUpdate,
)
from app.services.service_catalog_service import (
    CategoryNotFoundError,
    ServiceCatalogItemNotFoundError,
    SubcategoryMismatchError,
    create_item,
    get_item,
    list_items,
    update_item,
    CatalogItemFieldNotFoundError,
    add_field,
    list_fields,
    remove_field,
    update_field,
)

router = APIRouter(prefix="/service-catalog", tags=["service-catalog"])


@router.post(
    "", response_model=ServiceCatalogItemRead, status_code=status.HTTP_201_CREATED
)
def add_catalog_item(
    data: ServiceCatalogItemCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> ServiceCatalogItemRead:
    """Cria um item do catálogo de serviços. Restrito a administradores."""
    try:
        item = create_item(session, data)
    except (CategoryNotFoundError, SubcategoryMismatchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return ServiceCatalogItemRead.model_validate(item)


@router.get("", response_model=list[ServiceCatalogItemRead])
def get_catalog_items(
    category_id: int | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ServiceCatalogItemRead]:
    """Lista itens do catálogo visíveis ao usuário."""
    items = list_items(session, current_user, category_id)
    return [ServiceCatalogItemRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=ServiceCatalogItemRead)
def read_catalog_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ServiceCatalogItemRead:
    """Consulta um item específico do catálogo."""
    try:
        item = get_item(session, item_id, current_user)
    except ServiceCatalogItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return ServiceCatalogItemRead.model_validate(item)


@router.patch("/{item_id}", response_model=ServiceCatalogItemRead)
def edit_catalog_item(
    item_id: int,
    data: ServiceCatalogItemUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> ServiceCatalogItemRead:
    """Atualiza um item do catálogo (inclusive ativar/desativar). Restrito a administradores."""
    try:
        item = update_item(session, item_id, data)
    except ServiceCatalogItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except (CategoryNotFoundError, SubcategoryMismatchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return ServiceCatalogItemRead.model_validate(item)


@router.post(
    "/{item_id}/fields",
    response_model=CatalogItemFieldRead,
    status_code=status.HTTP_201_CREATED,
)
def add_catalog_item_field(
    item_id: int,
    data: CatalogItemFieldCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> CatalogItemFieldRead:
    """Adiciona um campo de formulário a um item do catálogo. Restrito a administradores."""
    try:
        field = add_field(session, item_id, data)
    except ServiceCatalogItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return CatalogItemFieldRead.model_validate(field)


@router.get("/{item_id}/fields", response_model=list[CatalogItemFieldRead])
def get_catalog_item_fields(
    item_id: int,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> list[CatalogItemFieldRead]:
    """Lista os campos de formulário de um item do catálogo."""
    try:
        fields = list_fields(session, item_id)
    except ServiceCatalogItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [CatalogItemFieldRead.model_validate(f) for f in fields]


@router.patch("/{item_id}/fields/{field_id}", response_model=CatalogItemFieldRead)
def edit_catalog_item_field(
    item_id: int,
    field_id: int,
    data: CatalogItemFieldUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> CatalogItemFieldRead:
    """Atualiza um campo de formulário existente. Restrito a administradores."""
    try:
        field = update_field(session, item_id, field_id, data)
    except CatalogItemFieldNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return CatalogItemFieldRead.model_validate(field)


@router.delete("/{item_id}/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_catalog_item_field(
    item_id: int,
    field_id: int,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> None:
    """Remove um campo de formulário de um item do catálogo. Restrito a administradores."""
    try:
        remove_field(session, item_id, field_id)
    except CatalogItemFieldNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
