"""Regras de negócio para configurações globais do sistema (linha única)."""

from sqlmodel import Session

from app.models.system_settings import SystemSettings
from app.schemas.system_settings import SystemSettingsUpdate

_SETTINGS_ID = 1


def get_settings(session: Session) -> SystemSettings:
    """Retorna a linha única de configurações, criando-a com padrão se não existir."""
    settings = session.get(SystemSettings, _SETTINGS_ID)
    if settings is None:
        settings = SystemSettings(id=_SETTINGS_ID)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def update_settings(session: Session, data: SystemSettingsUpdate) -> SystemSettings:
    """Atualiza as configurações globais."""
    settings = get_settings(session)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings