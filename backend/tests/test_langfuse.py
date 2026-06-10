"""Tests for Langfuse client bootstrap."""

from typing import Any

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.factory import create_app
from app.observability import langfuse as langfuse_module
from tests.conftest import FakeMcpClient, FakeReactRunner


def test_init_langfuse_creates_client() -> None:
    langfuse_module.shutdown_langfuse()
    settings = Settings(
        LANGFUSE_PUBLIC_KEY="pk-test",
        LANGFUSE_SECRET_KEY="sk-test",  # noqa: S106
        LANGFUSE_HOST="http://localhost:3001",
    )
    assert langfuse_module.init_langfuse(settings) is True
    callbacks = langfuse_module.build_callbacks(
        settings,
        session_id="00000000-0000-0000-0000-000000000001",
        channel="telegram",
    )
    assert len(callbacks) == 1
    langfuse_module.shutdown_langfuse()


def test_build_callbacks_empty_when_disabled() -> None:
    langfuse_module.shutdown_langfuse()
    settings = Settings(
        LANGFUSE_PUBLIC_KEY="",
        LANGFUSE_SECRET_KEY="",
        LANGFUSE_HOST="",
    )
    callbacks = langfuse_module.build_callbacks(
        settings,
        session_id="00000000-0000-0000-0000-000000000001",
        channel="web",
    )
    assert callbacks == []


def test_chat_returns_200_when_langfuse_disabled(monkeypatch: Any) -> None:
    """POST /chat succeeds when Langfuse is not configured."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")
    monkeypatch.setenv("LANGFUSE_HOST", "")
    get_settings.cache_clear()
    langfuse_module.shutdown_langfuse()

    app = create_app(
        mcp_client=FakeMcpClient(),  # type: ignore[arg-type]
        react_runner=FakeReactRunner(),  # type: ignore[arg-type]
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"message": "Привет", "channel": "web"},
        )

    assert response.status_code == 200
    get_settings.cache_clear()
    langfuse_module.shutdown_langfuse()
