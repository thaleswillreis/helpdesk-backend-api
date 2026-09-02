"""Configurações centrais da aplicação, lidas de variáveis de ambiente."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação (lidas de variáveis de ambiente ou .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_user: str = "helpdesk"
    postgres_password: str = "helpdesk"
    postgres_db: str = "helpdesk"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    test_postgres_db: str = "helpdesk_test"

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