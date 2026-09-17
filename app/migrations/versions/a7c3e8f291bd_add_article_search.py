"""add article.tags and full-text search_vector (trigger-maintained + GIN index)

Revision ID: a7c3e8f291bd
Revises: f4d8a1c6b923
Create Date: 2026-09-14 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a7c3e8f291bd'
down_revision: Union[str, Sequence[str], None] = 'f4d8a1c6b923'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "article",
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
    )

    # search_vector é uma coluna comum (não gerada), mantida por trigger — não
    # por GENERATED ALWAYS AS, porque to_tsvector(regconfig, text) é STABLE,
    # não IMMUTABLE, e colunas geradas exigem imutabilidade. Trigger é a forma
    # padrão do Postgres para manter tsvector sincronizado automaticamente.
    op.add_column("article", sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True))

    op.execute(
        """
        CREATE FUNCTION article_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(array_to_string(NEW.tags, ' '), '')), 'A') ||
                setweight(to_tsvector('portuguese', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('portuguese', coalesce(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER article_search_vector_trigger
        BEFORE INSERT OR UPDATE ON article
        FOR EACH ROW EXECUTE FUNCTION article_search_vector_update();
        """
    )

    # Preenche o vetor de busca de eventuais artigos já existentes (a trigger
    # só age em INSERT/UPDATE futuros).
    op.execute(
        """
        UPDATE article SET
            search_vector =
                setweight(to_tsvector('simple', coalesce(array_to_string(tags, ' '), '')), 'A') ||
                setweight(to_tsvector('portuguese', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('portuguese', coalesce(content, '')), 'B');
        """
    )

    op.execute(
        "CREATE INDEX ix_article_search_vector ON article USING GIN (search_vector)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_article_search_vector")
    op.execute("DROP TRIGGER IF EXISTS article_search_vector_trigger ON article")
    op.execute("DROP FUNCTION IF EXISTS article_search_vector_update()")
    op.drop_column("article", "search_vector")
    op.drop_column("article", "tags")