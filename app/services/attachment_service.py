"""Regras de negócio para upload/consulta de anexos de chamados."""

import io
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.core.config import settings
from app.core.storage import get_internal_client, get_public_client
from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.models.user import User


class TicketNotFoundError(Exception):
    """Levantado quando o chamado informado não existe."""


class AttachmentNotFoundError(Exception):
    """Levantado quando o anexo informado não existe."""


class InvalidFileExtensionError(Exception):
    """Levantado quando a extensão do arquivo não é permitida."""


class FileTooLargeError(Exception):
    """Levantado quando o arquivo excede o tamanho máximo permitido."""


def _extension_of(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def upload_attachment(
    session: Session,
    ticket_id: int,
    filename: str,
    content_type: str,
    file_bytes: bytes,
    uploader: User,
) -> TicketAttachment:
    """Valida e envia um arquivo para o MinIO, registrando os metadados no banco."""
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")

    extension = _extension_of(filename)
    if extension not in settings.allowed_attachment_extensions:
        raise InvalidFileExtensionError(
            f"Extensão '.{extension}' não permitida. Permitidas: "
            f"{', '.join(sorted(settings.allowed_attachment_extensions))}."
        )

    max_bytes = settings.max_attachment_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise FileTooLargeError(
            f"Arquivo excede o tamanho máximo de {settings.max_attachment_size_mb} MB."
        )

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    storage_key = f"{ticket_id}/{timestamp}_{safe_filename}"

    client = get_internal_client()
    client.put_object(
        settings.minio_bucket_name,
        storage_key,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )

    attachment = TicketAttachment(
        ticket_id=ticket_id,
        uploaded_by=uploader.id,
        original_filename=filename,
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=len(file_bytes),
    )
    session.add(attachment)
    session.commit()
    session.refresh(attachment)
    return attachment


def list_attachments(session: Session, ticket_id: int) -> list[TicketAttachment]:
    """Lista os anexos de um chamado."""
    query = select(TicketAttachment).where(TicketAttachment.ticket_id == ticket_id)
    return list(session.exec(query))


def get_download_url(session: Session, attachment_id: int) -> str:
    """Gera uma URL pré-assinada (válida por 1 hora) para download do anexo."""
    attachment = session.get(TicketAttachment, attachment_id)
    if attachment is None:
        raise AttachmentNotFoundError("Anexo não encontrado.")

    client = get_public_client()
    return client.presigned_get_object(
        settings.minio_bucket_name,
        attachment.storage_key,
        expires=timedelta(hours=1),
    )