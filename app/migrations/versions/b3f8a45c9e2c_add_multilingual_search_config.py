"""add multilingual (pt+en) text search configuration for articles

Revision ID: b3f8a45c9e2c
Revises: a7c3e8f291bd
Create Date: 2026-09-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b3f8a45c9e2c'
down_revision: Union[str, Sequence[str], None] = 'a7c3e8f291bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Configuração customizada: copia 'portuguese', mas troca o dicionário de
    # tokens puramente ASCII (tipicamente termos técnicos em inglês, ex.:
    # router/routers) para 'english_stem'. Sem isso, 'portuguese' aplicaria o
    # stemmer português também a essas palavras, que não reduz plurais em
    # inglês corretamente.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'helpdesk_ptbr') THEN
                CREATE TEXT SEARCH CONFIGURATION helpdesk_ptbr (COPY = pg_catalog.portuguese);
                ALTER TEXT SEARCH CONFIGURATION helpdesk_ptbr
                    ALTER MAPPING FOR asciiword, asciihword, hword_asciipart
                    WITH english_stem;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION article_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(array_to_string(NEW.tags, ' '), '')), 'A') ||
                setweight(to_tsvector('helpdesk_ptbr', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('helpdesk_ptbr', coalesce(NEW.content, '')), 'B');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
        """
    )

    # Recalcula o vetor de busca dos artigos já existentes com a nova configuração.
    op.execute(
        """
        UPDATE article SET
            search_vector =
                setweight(to_tsvector('simple', coalesce(array_to_string(tags, ' '), '')), 'A') ||
                setweight(to_tsvector('helpdesk_ptbr', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('helpdesk_ptbr', coalesce(content, '')), 'B');
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION article_search_vector_update() RETURNS trigger AS $$
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
    op.execute("DROP TEXT SEARCH CONFIGURATION IF EXISTS helpdesk_ptbr")