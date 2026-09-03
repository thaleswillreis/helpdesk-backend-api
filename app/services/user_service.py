"""Regras de negócio para gestão de usuários."""

from sqlmodel import Session, select

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user import UserCreate


class EmailAlreadyExistsError(Exception):
    """Levantado ao tentar criar um usuário com email já cadastrado."""


class RoleNotFoundError(Exception):
    """Levantado quando o papel informado não existe."""


def create_user(session: Session, data: UserCreate) -> User:
    """Cria um novo usuário, validando email único e papel existente."""
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing is not None:
        raise EmailAlreadyExistsError(f"Já existe um usuário com o email {data.email}.")

    role = session.exec(select(Role).where(Role.name == data.role_name)).first()
    if role is None:
        raise RoleNotFoundError(f"Papel '{data.role_name}' não encontrado.")

    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role_id=role.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user