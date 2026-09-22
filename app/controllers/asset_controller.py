"""Endpoints de gestão de ativos do CMDB e seus relacionamentos."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate
from app.schemas.asset_relationship import (
    AssetRelationshipCreate,
    AssetRelationshipRead,
)
from app.services.asset_service import (
    AssetNotFoundError,
    DuplicateRelationshipError,
    DuplicateSerialNumberError,
    InvalidResponsibleError,
    RelationshipNotFoundError,
    create_asset,
    create_relationship,
    delete_relationship,
    get_asset,
    list_assets,
    list_relationships,
    update_asset,
)

router = APIRouter(prefix="/assets", tags=["cmdb"])


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def add_asset(
    data: AssetCreate,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> AssetRead:
    """Cadastra um novo ativo. Restrito a admin/tecnico."""
    try:
        asset = create_asset(session, data)
    except DuplicateSerialNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidResponsibleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return AssetRead.model_validate(asset)


@router.get("", response_model=list[AssetRead])
def get_assets(
    asset_type: str | None = None,
    asset_status: str | None = None,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> list[AssetRead]:
    """Lista ativos, opcionalmente filtrando por tipo e/ou status. Restrito a admin/tecnico."""
    assets = list_assets(session, asset_type, asset_status)
    return [AssetRead.model_validate(a) for a in assets]


@router.get("/{asset_id}", response_model=AssetRead)
def read_asset(
    asset_id: int,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> AssetRead:
    """Consulta um ativo específico. Restrito a admin/tecnico."""
    try:
        asset = get_asset(session, asset_id)
    except AssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return AssetRead.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetRead)
def edit_asset(
    asset_id: int,
    data: AssetUpdate,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> AssetRead:
    """Atualiza um ativo existente. Restrito a admin/tecnico."""
    try:
        asset = update_asset(session, asset_id, data)
    except AssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except DuplicateSerialNumberError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except InvalidResponsibleError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return AssetRead.model_validate(asset)


@router.post(
    "/relationships",
    response_model=AssetRelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
def add_relationship(
    data: AssetRelationshipCreate,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> AssetRelationshipRead:
    """Cria um relacionamento de dependência entre dois ativos. Restrito a admin/tecnico."""
    try:
        relationship = create_relationship(session, data)
    except AssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DuplicateRelationshipError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return AssetRelationshipRead.model_validate(relationship)


@router.get("/{asset_id}/relationships", response_model=list[AssetRelationshipRead])
def read_relationships(
    asset_id: int,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> list[AssetRelationshipRead]:
    """Lista os relacionamentos de um ativo (como origem e como destino). Restrito a admin/tecnico."""
    try:
        relationships = list_relationships(session, asset_id)
    except AssetNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [AssetRelationshipRead.model_validate(r) for r in relationships]


@router.delete(
    "/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_relationship(
    relationship_id: int,
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> None:
    """Remove um relacionamento entre ativos. Restrito a admin/tecnico."""
    try:
        delete_relationship(session, relationship_id)
    except RelationshipNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
