"""Fixtures compartilhadas para os testes automatizados."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.core.database import get_session
from app.main import app

engine = create_engine(settings.test_database_url, echo=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Cria tabelas e papéis básicos no banco de testes antes da suíte."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        from app.models.role import Role

        for name in ("admin", "tecnico", "solicitante"):
            session.add(Role(name=name))
        session.commit()

        # search_vector é mantido por trigger no Postgres, não pelo SQLModel/ORM
        # (to_tsvector com configuração de idioma não é IMMUTABLE, então não pode
        # ser GENERATED ALWAYS AS). create_all() não recria esse recurso puramente
        # SQL, então replicamos aqui o mesmo DDL da migration a7c3e8f291bd.
        from sqlalchemy import text

        session.execute(
            text("ALTER TABLE article ADD COLUMN IF NOT EXISTS search_vector tsvector")
        )

        session.execute(
            text(
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
        )

        session.execute(
            text(
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
        )
        session.execute(
            text(
                """
                DROP TRIGGER IF EXISTS article_search_vector_trigger ON article;
                CREATE TRIGGER article_search_vector_trigger
                BEFORE INSERT OR UPDATE ON article
                FOR EACH ROW EXECUTE FUNCTION article_search_vector_update();
                """
            )
        )
        session.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_article_search_vector ON article USING GIN (search_vector)"
            )
        )
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    """Sessão de banco isolada por teste: abre uma transação e sempre dá rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    """Cliente de testes do FastAPI, usando a sessão transacional no lugar da real."""

    def get_session_override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(session: Session):
    """Factory de usuário de teste, vinculado a um papel pelo nome."""
    from sqlmodel import select

    from app.core.security import hash_password
    from app.models.role import Role
    from app.models.user import User

    def _make_user(
        email: str, password: str, role_name: str, is_vip: bool = False, level: str | None = None
    ) -> User:
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        user = User(
            name=f"Usuário {role_name}",
            email=email,
            hashed_password=hash_password(password),
            role_id=role.id if role else None,
            is_vip=is_vip,
            level=level,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    return _make_user


@pytest.fixture
def auth_headers(client: TestClient):
    """Factory que faz login e retorna o header Authorization pronto."""

    def _auth_headers(email: str, password: str) -> dict:
        response = client.post("/auth/login", data={"username": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers


@pytest.fixture
def make_category(session: Session):
    """Factory de categoria de teste."""
    from app.models.category import Category

    def _make_category(name: str, default_priority: str = "media") -> Category:
        category = Category(name=name, default_priority=default_priority)
        session.add(category)
        session.commit()
        session.refresh(category)
        return category

    return _make_category