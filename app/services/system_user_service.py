"""Acesso ao usuário 'sistema', usado como ator em decisões automatizadas."""

from sqlmodel import Session, select

from app.core.constants import SYSTEM_USER_EMAIL
from app.models.user import User


class SystemUserNotConfiguredError(Exception):
    """Levantado quando o usuário sistema não foi criado no banco (migration não aplicada)."""


def get_system_user(session: Session) -> User:
    """Retorna o usuário sistema, usado como autor de aprovações/rejeições automáticas."""
    user = session.exec(select(User).where(User.email == SYSTEM_USER_EMAIL)).first()
    if user is None:
        raise SystemUserNotConfiguredError(
            "Usuário sistema não encontrado. Verifique se a migration foi aplicada."
        )
    return user
