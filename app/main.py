from fastapi import FastAPI

from app.controllers.auth_controller import router as auth_router
from app.controllers.user_controller import router as user_router

app = FastAPI(
    title="Helpdesk API",
    description="Backend de um sistema de abertura de chamados.",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(user_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok"}