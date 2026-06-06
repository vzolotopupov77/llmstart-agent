"""Application configuration from environment variables."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENAI_BASE_URL",
    )
    openai_model: str = Field(default="openai/gpt-4o-mini", alias="OPENAI_MODEL")
    openai_timeout_seconds: int = Field(default=60, alias="OPENAI_TIMEOUT_SECONDS")

    data_dir: Path | None = Field(default=None, alias="DATA_DIR")
    mcp_server_cwd: Path = Field(default=REPO_ROOT / "mcp_server")

    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str | None = Field(default=None, alias="LANGFUSE_HOST")

    session_ttl_hours: int = Field(default=24, alias="SESSION_TTL_HOURS")
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3002"],
        alias="CORS_ORIGINS",
    )

    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    rag_top_k: int = Field(default=4, alias="RAG_TOP_K")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("data_dir", mode="before")
    @classmethod
    def resolve_data_dir(cls, value: str | Path | None) -> Path:
        if value is None or (isinstance(value, str) and not value.strip()):
            return REPO_ROOT / "data"
        return Path(value)

    @property
    def langfuse_enabled(self) -> bool:
        return bool(
            self.langfuse_public_key and self.langfuse_secret_key and self.langfuse_host,
        )

    def mcp_subprocess_env(self) -> dict[str, str]:
        """Environment passed to mcp_server subprocess."""
        env = os.environ.copy()
        env["DATA_DIR"] = str(self.data_dir)
        env["OPENAI_API_KEY"] = self.openai_api_key
        env["OPENAI_BASE_URL"] = self.openai_base_url
        env["EMBEDDING_MODEL"] = self.embedding_model
        env["RAG_TOP_K"] = str(self.rag_top_k)
        return env


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
