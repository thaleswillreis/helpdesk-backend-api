"""Contratos de entrada/saída para autenticação."""

from pydantic import BaseModel


class Token(BaseModel):
    """Par de tokens emitido no login ou na renovação."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Corpo da requisição para renovar o access token."""

    refresh_token: str