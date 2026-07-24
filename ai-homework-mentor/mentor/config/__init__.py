"""Загрузка config.yaml и переменных окружения."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).parent
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"

# Baseline orchestrator context growth per aspect in Sprint 03 (single-agent review).
SPRINT03_BASELINE_DELTA = 4500


class AppConfig(BaseSettings):
    """Конфигурация приложения: YAML-дефолты + перекрытие из .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    openrouter_api_key: str = Field(validation_alias="OPENROUTER_API_KEY")
    model: str = Field(default="google/gemini-2.5-flash", validation_alias="MODEL")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    output_mode: str = Field(default="verbose", validation_alias="OUTPUT_MODE")
    context_limit: int = Field(default=128_000, validation_alias="CONTEXT_LIMIT")
    summarization_threshold: int = Field(
        default=80_000,
        validation_alias="SUMMARIZATION_THRESHOLD",
    )
    agent_recursion_limit: int = Field(
        default=200,
        validation_alias="AGENT_RECURSION_LIMIT",
    )
    agent_max_attempts: int = Field(
        default=10,
        validation_alias="AGENT_MAX_ATTEMPTS",
    )
    llm_request_timeout: int = Field(
        default=600,
        validation_alias="LLM_REQUEST_TIMEOUT",
        description="Таймаут одного LLM-запроса (OpenRouter), секунды",
    )

    @property
    def config_path(self) -> Path:
        """Путь к YAML-файлу конфигурации."""
        return DEFAULT_CONFIG_PATH


def _load_yaml_defaults() -> dict[str, Any]:
    if not DEFAULT_CONFIG_PATH.exists():
        return {}
    with DEFAULT_CONFIG_PATH.open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return raw if isinstance(raw, dict) else {}


def load_app_config() -> AppConfig:
    """Загрузить конфиг; fail-fast при отсутствии OPENROUTER_API_KEY.

    Приоритет: .env / переменные окружения > config.yaml > дефолты полей.
    """
    yaml_defaults = _load_yaml_defaults()
    try:
        env_config = AppConfig()
        merged = {**yaml_defaults, **env_config.model_dump(exclude_unset=True)}
        return AppConfig(**merged)
    except ValidationError as exc:
        missing_key_fields = {"openrouter_api_key", "OPENROUTER_API_KEY"}
        for error in exc.errors():
            loc = error.get("loc", ())
            if loc and loc[-1] in missing_key_fields:
                message = "OPENROUTER_API_KEY is required. See .env.example"
                raise SystemExit(message) from exc
        raise
