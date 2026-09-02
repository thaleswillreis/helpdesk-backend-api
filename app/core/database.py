"""Configuração da engine e da sessão do banco de dados."""

from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False)


def get_session() -> Generator[Session, None, None]:
    """Fornece uma sessão de banco de dados por requisição (dependency injection)."""
    with Session(engine) as session:
        yield session