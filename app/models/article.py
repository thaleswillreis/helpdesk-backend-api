"""Modelo de dados para artigos da base de conhecimento."""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

from app.models.category import Category
from app.models.enums import ArticleStatus
from app.models.subcategory import Subcategory
from app.models.user import User


class Article(SQLModel, table=True):
    """Artigo/procedimento da base de conhecimento."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    content: str

    status: ArticleStatus = Field(default=ArticleStatus.DRAFT, index=True)

    category_id: int = Field(foreign_key="category.id")
    category: Category = Relationship()

    subcategory_id: int | None = Field(default=None, foreign_key="subcategory.id")
    subcategory: Subcategory | None = Relationship()

    author_id: int = Field(foreign_key="user.id")
    author: User = Relationship()

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))