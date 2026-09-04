"""Constantes e helpers de papéis, compartilhados entre dependencies e services."""

from app.models.user import User

STAFF_ROLES = {"admin", "tecnico"}


def is_staff(user: User) -> bool:
    """Retorna True se o usuário for admin ou técnico."""
    return user.role is not None and user.role.name in STAFF_ROLES