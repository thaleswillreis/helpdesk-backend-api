"""Modelo de dados para o vínculo entre chamados e ativos do CMDB (impacto)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class TicketAsset(SQLModel, table=True):
    """Vínculo manual entre um chamado e um ativo afetado."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    asset_id: int = Field(foreign_key="asset.id", index=True)

    linked_by: int = Field(foreign_key="user.id")
    linked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
