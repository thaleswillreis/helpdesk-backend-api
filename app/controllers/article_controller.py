"""Endpoints de gestão de artigos da base de conhecimento."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleRead, ArticleUpdate
from app.services.article_service import (
    ArticleNotFoundError,
    CategoryNotFoundError,
    SubcategoryMismatchError,
    create_article,
    get_article,
    list_articles,
    update_article,
)

router = APIRouter(prefix="/articles", tags=["knowledge-base"])


@router.post("", response_model=ArticleRead, status_code=status.HTTP_201_CREATED)
def add_article(
    data: ArticleCreate,
    session: Session = Depends(get_session),
    staff: User = Depends(require_role("admin", "tecnico")),
) -> ArticleRead:
    """Cria um artigo. Restrito a admin/tecnico."""
    try:
        article = create_article(session, data, staff)
    except (CategoryNotFoundError, SubcategoryMismatchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return ArticleRead.model_validate(article)


@router.get("", response_model=list[ArticleRead])
def get_articles(
    category_id: int | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ArticleRead]:
    """Lista artigos visíveis ao usuário, opcionalmente filtrando por categoria."""
    articles = list_articles(session, current_user, category_id)
    return [ArticleRead.model_validate(a) for a in articles]


@router.get("/{article_id}", response_model=ArticleRead)
def read_article(
    article_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ArticleRead:
    """Consulta um artigo específico."""
    try:
        article = get_article(session, article_id, current_user)
    except ArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return ArticleRead.model_validate(article)


@router.patch("/{article_id}", response_model=ArticleRead)
def edit_article(
    article_id: int,
    data: ArticleUpdate,
    session: Session = Depends(get_session),
    _staff: User = Depends(require_role("admin", "tecnico")),
) -> ArticleRead:
    """Atualiza um artigo. Restrito a admin/tecnico."""
    try:
        article = update_article(session, article_id, data)
    except ArticleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (CategoryNotFoundError, SubcategoryMismatchError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return ArticleRead.model_validate(article)