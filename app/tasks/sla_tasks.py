"""Tarefa periódica do Celery Beat: verifica transições de SLA e dispara alertas."""

from sqlmodel import Session

from app.core.celery_app import celery_app
from app.core.database import engine
from app.services.sla_notification_service import check_sla_transitions


@celery_app.task(name="check_sla_notifications")
def check_sla_notifications() -> None:
    """Ponto de entrada do Celery: abre a sessão real e delega à lógica testável."""
    with Session(engine) as session:
        check_sla_transitions(session)
