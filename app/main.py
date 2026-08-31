"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI

app = FastAPI(
    title="Helpdesk API",
    description="Backend de um sistema de abertura de chamados.",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Endpoint simples para verificar se a API está no ar."""
    return {"status": "ok"}