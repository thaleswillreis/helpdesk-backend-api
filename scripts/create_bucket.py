"""Cria o bucket de anexos no object storage, se ainda não existir.

Uso: uv run python -m scripts.create_bucket
"""

from app.core.config import settings
from app.core.storage import ensure_bucket


def main() -> None:
    """Garante a existência do bucket configurado."""
    ensure_bucket()
    print(f"Bucket '{settings.minio_bucket_name}' pronto.")


if __name__ == "__main__":
    main()
