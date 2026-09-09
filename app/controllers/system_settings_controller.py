"""Endpoints de configurações globais do sistema."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.dependencies import require_role
from app.schemas.system_settings import SystemSettingsRead, SystemSettingsUpdate
from app.services.system_settings_service import get_settings, update_settings

router = APIRouter(prefix="/system-settings", tags=["settings"])


@router.get("", response_model=SystemSettingsRead)
def read_settings(
    session: Session = Depends(get_session),
    _staff=Depends(require_role("admin", "tecnico")),
) -> SystemSettingsRead:
    """Consulta as configurações globais atuais. Restrito a admin/tecnico."""
    return SystemSettingsRead.model_validate(get_settings(session))


@router.patch("", response_model=SystemSettingsRead)
def edit_settings(
    data: SystemSettingsUpdate,
    session: Session = Depends(get_session),
    _admin=Depends(require_role("admin")),
) -> SystemSettingsRead:
    """Atualiza as configurações globais. Restrito a administradores."""
    return SystemSettingsRead.model_validate(update_settings(session, data))