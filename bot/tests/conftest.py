"""Shared pytest fixtures."""

import pytest

from bot.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _bot_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token:12345")
    monkeypatch.setenv("BACKEND_BASE_URL", "http://testserver")
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    return Settings()
