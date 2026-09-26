from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
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

    database_url: str = (
        "postgresql+asyncpg://genai:genai@localhost:5432/genai"
    )

    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()