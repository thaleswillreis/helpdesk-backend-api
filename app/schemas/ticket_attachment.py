"""Contratos de saída para anexos de chamados."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketAttachmentRead(BaseModel):
    """Metadados públicos de um anexo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    size_bytes: int
    uploaded_by: int
    uploaded_at: datetime


class TicketAttachmentDownload(BaseModel):
    """Resposta contendo a URL de download temporária do anexo."""

    download_url: str