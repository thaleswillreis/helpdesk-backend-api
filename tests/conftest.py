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
    """Cria todas as tabelas no banco de testes antes da suíte e as remove ao final."""
    SQLModel.metadata.create_all(engine)
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

    def _make_user(email: str, password: str, role_name: str) -> User:
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        user = User(
            name=f"Usuário {role_name}",
            email=email,
            hashed_password=hash_password(password),
            role_id=role.id if role else None,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    return _make_user


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Cria tabelas e papéis básicos no banco de testes antes da suíte."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        from app.models.role import Role

        for name in ("admin", "tecnico", "solicitante"):
            session.add(Role(name=name))
        session.commit()

    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def auth_headers(client: TestClient):
    """Factory que faz login e retorna o header Authorization pronto."""

    def _auth_headers(email: str, password: str) -> dict:
        response = client.post("/auth/login", data={"username": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers