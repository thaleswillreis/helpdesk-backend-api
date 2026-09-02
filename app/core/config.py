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

    @property
    def database_url(self) -> str:
        """Monta a URL de conexão do SQLAlchemy/SQLModel a partir das partes."""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

settings = Settings()