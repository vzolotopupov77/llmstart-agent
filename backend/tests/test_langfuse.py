"""Tests for Langfuse client bootstrap."""

from app.core.config import Settings
from app.observability import langfuse as langfuse_module


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
