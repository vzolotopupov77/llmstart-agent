"""MCP server configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_data_dir() -> Path:
    """Resolve repo `data/` from package location unless overridden."""
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data"


class Settings(BaseSettings):
    """Runtime settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=_default_data_dir, alias="DATA_DIR")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENAI_BASE_URL",
    )
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )
    rag_top_k: int = Field(default=4, alias="RAG_TOP_K")
    chunk_size: int = Field(default=800, alias="RAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="RAG_CHUNK_OVERLAP")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
