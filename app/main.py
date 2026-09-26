from fastapi import FastAPI

from app.controllers.article_controller import router as article_router
from app.controllers.asset_controller import router as asset_router
from app.controllers.auth_controller import router as auth_router
from app.controllers.category_controller import router as category_router
from app.controllers.dashboard_controller import router as dashboard_router
from app.controllers.export_controller import router as export_router
from app.controllers.kpi_controller import router as kpi_router
from app.controllers.service_catalog_controller import router as service_catalog_router
from app.controllers.sla_policy_controller import router as sla_policy_router
from app.controllers.system_settings_controller import router as system_settings_router
from app.controllers.team_controller import router as team_router
from app.controllers.ticket_controller import router as ticket_router
from app.controllers.triage_rule_controller import router as triage_rule_router
from app.controllers.user_controller import router as user_router
from app.controllers.webhook_subscription_controller import (
    router as webhook_subscription_router,
)

tags_metadata = [
    {"name": "health", "description": "Verificação de disponibilidade da API."},
    {"name": "auth", "description": "Autenticação: login, refresh token e usuário autenticado."},
    {"name": "users", "description": "Cadastro e gestão de usuários (restrito a administradores)."},
    {"name": "categories", "description": "Categorias e subcategorias de classificação de chamados."},
    {"name": "teams", "description": "Equipes de atendimento, membros e expediente."},
    {"name": "tickets", "description": "Ciclo de vida completo dos chamados: CRUD, histórico, comentários, anexos, SLA, vínculo com artigos e ativos, catálogo e aprovação."},
    {"name": "knowledge-base", "description": "Artigos da base de conhecimento, com busca full-text bilíngue."},
    {"name": "service-catalog", "description": "Catálogo de serviços com formulários tipados e fluxo de aprovação."},
    {"name": "automation", "description": "Motor de regras de triagem e assinaturas de webhook."},
    {"name": "settings", "description": "Configurações globais do sistema (ex.: limiar de risco de SLA)."},
    {"name": "sla", "description": "Políticas de SLA por prioridade."},
    {"name": "cmdb", "description": "Ativos de TI e relacionamentos de dependência (CMDB)."},
    {"name": "dashboard", "description": "Indicadores agregados, KPIs e exportação de dados em CSV."},
]

app = FastAPI(
    title="Helpdesk API",
    description=(
        "Backend de um sistema de abertura e gestão de chamados (Helpdesk/ITSM), "
        "construído em camadas (Controllers/Services/Models) com FastAPI.\n\n"
        "Cobre autenticação e RBAC, gestão de chamados com escalonamento por nível, "
        "cálculo de SLA respeitando expediente por equipe, base de conhecimento com "
        "busca full-text, catálogo de serviços com aprovação, CMDB, automação via "
        "webhooks e Celery, e indicadores de gestão.\n\n"
        "Repositório: https://github.com/thaleswillreis/helpdesk-backend-api"
    ),
    version="1.0.0",
    contact={"name": "Thales Will S. Reis", "url": "https://github.com/thaleswillreis"},
    license_info={"name": "MIT", "url": "https://github.com/thaleswillreis/helpdesk-backend-api/blob/main/LICENSE"},
    openapi_tags=tags_metadata,
)

app.include_router(article_router)
app.include_router(asset_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(category_router)
app.include_router(service_catalog_router)
app.include_router(sla_policy_router)
app.include_router(system_settings_router)
app.include_router(team_router)
app.include_router(ticket_router)
app.include_router(triage_rule_router)
app.include_router(webhook_subscription_router)
app.include_router(dashboard_router)
app.include_router(kpi_router)
app.include_router(export_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok"}
