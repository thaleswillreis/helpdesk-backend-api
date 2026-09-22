"""Configuração do Celery para processamento assíncrono (webhooks e automações)."""

from celery import Celery

from app.core.config import settings

celery_app = Celery("helpdesk", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

celery_app.conf.beat_schedule = {
    "check-approval-timeouts-every-5-minutes": {
        "task": "check_approval_timeouts",
        "schedule": 300.0,
    },
}

# Importado ao final, depois de celery_app já criado e configurado: garante que
# o worker (subido isoladamente via `celery -A app.core.celery_app worker`)
# conheça as tarefas definidas nesses módulos. Sem isso, o worker rejeitaria
# as tarefas com "Received unregistered task" — a instância do Celery só sabe
# de tarefas cujos módulos foram de fato importados neste processo.
from app.tasks import approval_tasks, webhook_tasks  # noqa: E402, F401