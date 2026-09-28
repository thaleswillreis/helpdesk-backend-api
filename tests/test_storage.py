"""Testes de integração do object storage (requer o serviço de storage ativo)."""

import io
from datetime import timedelta

import httpx

import app.core.storage as storage
from app.core.config import settings


def test_ensure_bucket_is_idempotent() -> None:
    """Chamar ensure_bucket duas vezes contra o servidor não deve falhar."""
    storage.ensure_bucket()
    storage._bucket_ready = False  # força uma nova checagem contra o servidor
    storage.ensure_bucket()

    assert storage.get_internal_client().bucket_exists(settings.minio_bucket_name)


def test_presigned_url_serves_uploaded_object() -> None:
    """A URL pré-assinada deve ser aceita pelo servidor e devolver o conteúdo enviado."""
    storage.ensure_bucket()
    key = "tests/presigned-check.txt"
    content = b"conteudo-de-teste"
    internal = storage.get_internal_client()

    internal.put_object(
        settings.minio_bucket_name,
        key,
        io.BytesIO(content),
        length=len(content),
        content_type="text/plain",
    )
    try:
        url = storage.get_public_client().presigned_get_object(
            settings.minio_bucket_name, key, expires=timedelta(minutes=5)
        )
        response = httpx.get(url, timeout=10)

        assert response.status_code == 200
        assert response.content == content
    finally:
        internal.remove_object(settings.minio_bucket_name, key)
