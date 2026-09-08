"""Regras de negócio para categorias e subcategorias."""

from sqlmodel import Session, select

from app.models.category import Category
from app.models.subcategory import Subcategory
from app.models.team import Team
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    SubcategoryCreate,
    SubcategoryUpdate,
)


class CategoryNotFoundError(Exception):
    """Levantado quando a categoria informada não existe."""


class SubcategoryNotFoundError(Exception):
    """Levantado quando a subcategoria informada não existe."""


class DuplicateCategoryNameError(Exception):
    """Levantado ao tentar criar/renomear categoria para um nome já usado."""

class TeamNotFoundError(Exception):
    """Levantado quando a equipe informada não existe."""


def create_category(session: Session, data: CategoryCreate) -> Category:
    """Cria uma nova categoria."""
    existing = session.exec(select(Category).where(Category.name == data.name)).first()
    if existing is not None:
        raise DuplicateCategoryNameError(f"Já existe uma categoria chamada '{data.name}'.")

    if data.default_team_id is not None and session.get(Team, data.default_team_id) is None:
        raise TeamNotFoundError("Equipe informada não encontrada.")

    category = Category(
        name=data.name,
        default_priority=data.default_priority,
        default_team_id=data.default_team_id,
    )
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def list_categories(session: Session) -> list[Category]:
    """Lista todas as categorias."""
    return list(session.exec(select(Category)))


def update_category(session: Session, category_id: int, data: CategoryUpdate) -> Category:
    """Atualiza uma categoria existente."""
    category = session.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError("Categoria não encontrada.")

    if data.default_team_id is not None and session.get(Team, data.default_team_id) is None:
        raise TeamNotFoundError("Equipe informada não encontrada.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def create_subcategory(session: Session, data: SubcategoryCreate) -> Subcategory:
    """Cria uma nova subcategoria, validando que a categoria pai existe."""
    category = session.get(Category, data.category_id)
    if category is None:
        raise CategoryNotFoundError("Categoria informada não encontrada.")

    subcategory = Subcategory(name=data.name, category_id=data.category_id)
    session.add(subcategory)
    session.commit()
    session.refresh(subcategory)
    return subcategory


def list_subcategories(session: Session, category_id: int | None = None) -> list[Subcategory]:
    """Lista subcategorias, opcionalmente filtrando por categoria."""
    query = select(Subcategory)
    if category_id is not None:
        query = query.where(Subcategory.category_id == category_id)
    return list(session.exec(query))


def update_subcategory(
    session: Session, subcategory_id: int, data: SubcategoryUpdate
) -> Subcategory:
    """Atualiza uma subcategoria existente."""
    subcategory = session.get(Subcategory, subcategory_id)
    if subcategory is None:
        raise SubcategoryNotFoundError("Subcategoria não encontrada.")

    if data.category_id is not None and session.get(Category, data.category_id) is None:
        raise CategoryNotFoundError("Categoria informada não encontrada.")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subcategory, field, value)

    session.add(subcategory)
    session.commit()
    session.refresh(subcategory)
    return subcategory