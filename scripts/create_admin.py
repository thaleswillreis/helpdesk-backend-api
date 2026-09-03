"""Script para criar o primeiro usuário administrador do sistema.

Uso: uv run python scripts/create_admin.py
"""

import getpass
import sys

from sqlmodel import Session, select

from app.core.database import engine
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


def main() -> None:
    """Cria um usuário admin interativamente, validando duplicidade."""
    with Session(engine) as session:
        admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
        if admin_role is None:
            print("Papel 'admin' não encontrado. Rode as migrations antes: uv run alembic upgrade head")
            sys.exit(1)

        name = input("Nome do administrador: ").strip()
        email = input("Email do administrador: ").strip()

        existing = session.exec(select(User).where(User.email == email)).first()
        if existing is not None:
            print(f"Já existe um usuário com o email {email}.")
            sys.exit(1)

        password = getpass.getpass("Senha: ")
        confirm = getpass.getpass("Confirme a senha: ")
        if password != confirm:
            print("As senhas não conferem.")
            sys.exit(1)

        admin = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            role_id=admin_role.id,
        )
        session.add(admin)
        session.commit()

        print(f"Administrador '{email}' criado com sucesso.")


if __name__ == "__main__":
    main()