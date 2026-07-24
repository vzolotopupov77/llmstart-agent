"""Тесты фабрики ChatOpenRouter."""

from __future__ import annotations

import pytest

from mentor.config import AppConfig
from mentor.openrouter import build_chat_model


def test_build_chat_model_timeout_ms(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    config = AppConfig(llm_request_timeout=120)
    model = build_chat_model(config)
    assert model.request_timeout == 120_000
    assert model.model_name == "google/gemini-2.5-flash"


def test_build_chat_model_strips_openrouter_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("MODEL", "openrouter:anthropic/claude-sonnet-4")
    config = AppConfig()
    model = build_chat_model(config)
    assert model.model_name == "anthropic/claude-sonnet-4"
