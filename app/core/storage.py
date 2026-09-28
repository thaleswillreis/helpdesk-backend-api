"""Clientes S3 para upload, download e geração de links de anexos.

O SDK `minio` fala o protocolo S3 e funciona com qualquer servidor compatível
(hoje, RustFS). O prefixo MINIO_* das variáveis de ambiente é herdado do SDK.
"""

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

# Região fixa: evita uma consulta ao servidor só para descobrir a região do
# bucket, e não depende de o servidor implementar essa chamada.
_REGION = "us-east-1"

# Operações internas (upload/leitura): usa o endpoint alcançável a partir de
# onde a API está rodando (rede Docker ou localhost, conforme o ambiente).
_internal_client = Minio(
    settings.minio_internal_endpoint,
    access_key=settings.minio_root_user,
    secret_key=settings.minio_root_password,
    secure=settings.minio_secure,
    region=_REGION,
)

# Geração de URLs pré-assinadas: precisa do endpoint que o NAVEGADOR do
# usuário consegue alcançar. Em produção esse endpoint é HTTPS (via Caddy),
# enquanto o tráfego interno segue em HTTP, por isso a flag própria.
_public_client = Minio(
    settings.minio_public_endpoint,
    access_key=settings.minio_root_user,
    secret_key=settings.minio_root_password,
    secure=settings.minio_public_secure,
    region=_REGION,
)

_BUCKET_EXISTS_CODES = {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}
_bucket_ready = False


def get_internal_client() -> Minio:
    """Cliente para upload/leitura direta de objetos."""
    return _internal_client


def get_public_client() -> Minio:
    """Cliente para assinar URLs de download acessíveis pelo navegador."""
    return _public_client


def ensure_bucket() -> None:
    """Garante que o bucket de anexos exista (idempotente e seguro sob concorrência)."""
    global _bucket_ready
    if _bucket_ready:
        return

    if not _internal_client.bucket_exists(settings.minio_bucket_name):
        try:
            _internal_client.make_bucket(settings.minio_bucket_name)
        except S3Error as exc:
            # Outro processo pode ter criado o bucket entre a checagem e a criação.
            if exc.code not in _BUCKET_EXISTS_CODES:
                raise

    _bucket_ready = True
