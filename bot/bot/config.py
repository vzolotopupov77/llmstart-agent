"""Bot configuration from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str = Field(default="", alias="TELEGRAM_BOT_USERNAME")
    backend_base_url: str = Field(
        default="http://127.0.0.1:8003",
        alias="BACKEND_BASE_URL",
    )
    chat_timeout_seconds: int = Field(default=120, alias="BOT_CHAT_TIMEOUT_SECONDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("telegram_bot_token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "TELEGRAM_BOT_TOKEN is required"
            raise ValueError(msg)
        return stripped

    @field_validator("backend_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
