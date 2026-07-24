"""Smoke-тесты конфигурации."""

from __future__ import annotations

from pathlib import Path

import pytest

from mentor.config import AppConfig, load_app_config


def test_load_app_config_with_api_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    config = load_app_config()
    assert config.openrouter_api_key == "test-key"
    assert config.model == "google/gemini-2.5-flash"


def test_load_app_config_missing_api_key(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(SystemExit, match="OPENROUTER_API_KEY is required"):
        load_app_config()


def test_model_env_overrides_yaml(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    config = load_app_config()
    assert config.model == "meta-llama/llama-3.3-70b-instruct:free"


def test_yaml_defaults_applied_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    config = AppConfig()
    assert config.context_limit == 128_000
    assert config.summarization_threshold == 80_000
    assert config.agent_recursion_limit == 200
    assert config.agent_max_attempts == 10
    assert config.llm_request_timeout == 600
