"""Endpoints de gestão de categorias e subcategorias."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    SubcategoryCreate,
    SubcategoryRead,
    SubcategoryUpdate,
)
from app.services.category_service import (
    CategoryNotFoundError,
    DuplicateCategoryNameError,
    SubcategoryNotFoundError,
    TeamNotFoundError,
    create_category,
    create_subcategory,
    list_categories,
    list_subcategories,
    update_category,
    update_subcategory,
)

router = APIRouter(tags=["categories"])


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def add_category(
    data: CategoryCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> CategoryRead:
    """Cria uma nova categoria. Restrito a administradores."""
    try:
        category = create_category(session, data)
    except DuplicateCategoryNameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return CategoryRead.model_validate(category)


@router.get("/categories", response_model=list[CategoryRead])
def get_categories(
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> list[CategoryRead]:
    """Lista todas as categorias. Qualquer usuário autenticado pode consultar."""
    return [CategoryRead.model_validate(c) for c in list_categories(session)]


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def edit_category(
    category_id: int,
    data: CategoryUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> CategoryRead:
    """Atualiza uma categoria existente. Restrito a administradores."""
    try:
        category = update_category(session, category_id, data)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return CategoryRead.model_validate(category)


@router.post("/subcategories", response_model=SubcategoryRead, status_code=status.HTTP_201_CREATED)
def add_subcategory(
    data: SubcategoryCreate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> SubcategoryRead:
    """Cria uma nova subcategoria. Restrito a administradores."""
    try:
        subcategory = create_subcategory(session, data)
    except CategoryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return SubcategoryRead.model_validate(subcategory)


@router.get("/subcategories", response_model=list[SubcategoryRead])
def get_subcategories(
    category_id: int | None = None,
    session: Session = Depends(get_session),
    _user=Depends(get_current_user),
) -> list[SubcategoryRead]:
    """Lista subcategorias, opcionalmente filtrando por categoria."""
    return [
        SubcategoryRead.model_validate(s) for s in list_subcategories(session, category_id)
    ]


@router.patch("/subcategories/{subcategory_id}", response_model=SubcategoryRead)
def edit_subcategory(
    subcategory_id: int,
    data: SubcategoryUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> SubcategoryRead:
    """Atualiza uma subcategoria existente. Restrito a administradores."""
    try:
        subcategory = update_subcategory(session, subcategory_id, data)
    except (CategoryNotFoundError, SubcategoryNotFoundError) as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if isinstance(exc, SubcategoryNotFoundError)
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return SubcategoryRead.model_validate(subcategory)