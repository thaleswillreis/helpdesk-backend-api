"""Configurações centrais da aplicação, lidas de variáveis de ambiente."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação (lidas de variáveis de ambiente ou .env).

    Campos sem valor padrão são OBRIGATÓRIOS: se não vierem do .env ou do
    ambiente, a aplicação falha ao iniciar em vez de usar um segredo fraco
    silenciosamente.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Segredos: sem valor padrão, obrigatórios via .env ---
    postgres_password: str
    minio_root_password: str
    secret_key: str

    # --- Configuração não sensível: valor padrão OK ---
    postgres_user: str = "helpdesk"
    postgres_db: str = "helpdesk"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    test_postgres_db: str = "helpdesk_test"

    minio_root_user: str = "helpdesk"
    minio_bucket_name: str = "helpdesk-attachments"
    minio_internal_endpoint: str = "localhost:9010"
    minio_public_endpoint: str = "localhost:9010"
    minio_secure: bool = False

    max_attachment_size_mb: int = 10
    allowed_attachment_extensions: set[str] = {
        "jpg", "jpeg", "png", "gif", "pdf", "doc", "docx", "xls", "xlsx", "txt", "zip",
    }

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @property
    def database_url(self) -> str:
        """Monta a URL de conexão do SQLAlchemy/SQLModel a partir das partes."""
        return self._build_url(self.postgres_db)

    @property
    def test_database_url(self) -> str:
        """Monta a URL de conexão do banco de testes."""
        return self._build_url(self.test_postgres_db)

    def _build_url(self, database: str) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{database}"
        )


settings = Settings()