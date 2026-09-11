"""Regras de negócio para artigos da base de conhecimento."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core.roles import is_staff
from app.models.article import Article
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.models.user import User
from app.schemas.article import ArticleCreate, ArticleUpdate


class ArticleNotFoundError(Exception):
    """Levantado quando o artigo informado não existe ou não é visível ao usuário."""


class CategoryNotFoundError(Exception):
    """Levantado quando a categoria informada não existe."""


class SubcategoryMismatchError(Exception):
    """Levantado quando a subcategoria informada não pertence à categoria informada."""


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


def create_article(session: Session, data: ArticleCreate, author: User) -> Article:
    """Cria um artigo da base de conhecimento."""
    _validate_category(session, data.category_id, data.subcategory_id)

    article = Article(
        title=data.title,
        content=data.content,
        status=data.status,
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        author_id=author.id,
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    return article


def list_articles(
    session: Session, current_user: User, category_id: int | None = None
) -> list[Article]:
    """Lista artigos: staff vê tudo; solicitante só vê publicados."""
    query = select(Article)
    if not is_staff(current_user):
        query = query.where(Article.status == "published")
    if category_id is not None:
        query = query.where(Article.category_id == category_id)

    return list(session.exec(query))


def get_article(session: Session, article_id: int, current_user: User) -> Article:
    """Busca um artigo por id, respeitando a visibilidade por status."""
    article = session.get(Article, article_id)
    if article is None:
        raise ArticleNotFoundError("Artigo não encontrado.")

    if not is_staff(current_user) and article.status != "published":
        raise ArticleNotFoundError("Artigo não encontrado.")

    return article


def update_article(session: Session, article_id: int, data: ArticleUpdate) -> Article:
    """Atualiza um artigo existente. O controller já restringe isso a admin/tecnico."""
    article = session.get(Article, article_id)
    if article is None:
        raise ArticleNotFoundError("Artigo não encontrado.")

    final_category_id = data.category_id if data.category_id is not None else article.category_id
    final_subcategory_id = (
        data.subcategory_id if data.subcategory_id is not None else article.subcategory_id
    )
    if data.category_id is not None or data.subcategory_id is not None:
        _validate_category(session, final_category_id, final_subcategory_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    article.updated_at = datetime.now(UTC)

    session.add(article)
    session.commit()
    session.refresh(article)
    return article