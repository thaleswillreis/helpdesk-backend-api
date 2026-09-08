"""Modelo de dados para anexos de um chamado, armazenados no MinIO."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class TicketAttachment(SQLModel, table=True):
    """Metadados de um arquivo anexado a um chamado."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    uploaded_by: int = Field(foreign_key="user.id")

    original_filename: str = Field(max_length=255)
    storage_key: str = Field(max_length=500)
    content_type: str = Field(max_length=100)
    size_bytes: int

    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))