"""Configuração do Celery para processamento assíncrono (envio de notificações via webhook)."""

from celery import Celery

from app.core.config import settings

celery_app = Celery("helpdesk", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
