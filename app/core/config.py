from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal[
    "local",
    "development",
    "test",
    "production",
]


class Settings(BaseSettings):
    """Validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )

    app_name: str = "Enterprise GenAI Lab"
    app_version: str = "0.1.0"

    environment: Environment = "local"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    database_url: str | None = None

    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    openai_generation_model: str = "gpt-5.6-luna"
    openai_embedding_model: str = "text-embedding-3-small"
    retrieval_top_k: int = Field(default=5, gt=0, le=50)

    @model_validator(mode="after")
    def require_production_database(self) -> "Settings":
        if self.environment == "production" and self.database_url is None:
            raise ValueError("DATABASE_URL is required in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
