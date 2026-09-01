"""Configuração da engine e da sessão do banco de dados."""

from collections.abc import Generator

from sqlmodel import Session, create_engine

DATABASE_URL = "sqlite:///./helpdesk.db"

engine = create_engine(DATABASE_URL, echo=False)


def get_session() -> Generator[Session, None, None]:
    """Fornece uma sessão de banco de dados por requisição (dependency injection)."""
    with Session(engine) as session:
        yield session