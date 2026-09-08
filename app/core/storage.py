"""Clientes MinIO para upload, download e geração de links de anexos."""

from minio import Minio

from app.core.config import settings

# Operações internas (upload/delete): usa o endpoint alcançável a partir de
# onde a API está rodando (rede Docker ou localhost, dependendo do ambiente).
_internal_client = Minio(
    settings.minio_internal_endpoint,
    access_key=settings.minio_root_user,
    secret_key=settings.minio_root_password,
    secure=settings.minio_secure,
)

# Geração de URLs pré-assinadas: precisa do endpoint que o NAVEGADOR do
# usuário consegue alcançar (sempre localhost:9010, nunca o nome interno do Docker).
_public_client = Minio(
    settings.minio_public_endpoint,
    access_key=settings.minio_root_user,
    secret_key=settings.minio_root_password,
    secure=settings.minio_secure,
)


def get_internal_client() -> Minio:
    """Cliente para upload/leitura direta de objetos."""
    return _internal_client


def get_public_client() -> Minio:
    """Cliente para assinar URLs de download acessíveis pelo navegador."""
    return _public_client