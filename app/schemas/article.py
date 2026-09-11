"""Contratos de entrada/saída para artigos da base de conhecimento."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ArticleStatus


class ArticleCreate(BaseModel):
    """Dados para criar um artigo."""

    title: str = Field(max_length=200)
    content: str = Field(min_length=1)
    category_id: int
    subcategory_id: int | None = None
    status: ArticleStatus = ArticleStatus.DRAFT


class ArticleUpdate(BaseModel):
    """Campos que podem ser atualizados em um artigo."""

    title: str | None = Field(default=None, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    category_id: int | None = None
    subcategory_id: int | None = None
    status: ArticleStatus | None = None


class ArticleRead(BaseModel):
    """Dados públicos de um artigo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    status: ArticleStatus
    category_id: int
    subcategory_id: int | None
    author_id: int
    created_at: datetime
    updated_at: datetime