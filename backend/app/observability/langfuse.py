"""Langfuse tracing integration (SDK v3)."""

import logging
import os
from typing import Any

from langchain_core.callbacks.base import BaseCallbackHandler

from app.core.config import Settings

logger = logging.getLogger(__name__)

_langfuse_client: Any | None = None


def _sync_langfuse_env(settings: Settings) -> None:
    """Ensure Langfuse SDK reads credentials from the environment."""
    if settings.langfuse_public_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    if settings.langfuse_secret_key:
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    if settings.langfuse_host:
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        os.environ["LANGFUSE_BASE_URL"] = settings.langfuse_host


def init_langfuse(settings: Settings) -> bool:
    """Initialize singleton Langfuse client (required for CallbackHandler)."""
    global _langfuse_client  # noqa: PLW0603

    if not settings.langfuse_enabled:
        logger.info("Langfuse tracing disabled: LANGFUSE_* env incomplete")
        return False

    if _langfuse_client is not None:
        return True

    try:
        from langfuse import Langfuse
    except ImportError:
        logger.warning("Langfuse package is not available")
        return False

    try:
        _sync_langfuse_env(settings)
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:
        logger.warning("Failed to initialize Langfuse client", exc_info=True)
        _langfuse_client = None
        return False

    logger.info("Langfuse client initialized (host=%s)", settings.langfuse_host)
    return True


def flush_callbacks(callbacks: list[BaseCallbackHandler]) -> None:
    """Flush Langfuse events after a chat turn."""
    del callbacks

    if _langfuse_client is None:
        return

    try:
        _langfuse_client.flush()
    except Exception:
        logger.warning("Langfuse flush failed", exc_info=True)


def shutdown_langfuse() -> None:
    """Flush pending events and release Langfuse client."""
    global _langfuse_client  # noqa: PLW0603

    if _langfuse_client is None:
        return

    try:
        _langfuse_client.flush()
        _langfuse_client.shutdown()
    except Exception:
        logger.warning("Langfuse shutdown failed", exc_info=True)
    finally:
        _langfuse_client = None


def build_langfuse_metadata(*, session_id: str, channel: str) -> dict[str, str | list[str]]:
    """Runnable metadata for LangChain → Langfuse trace attributes."""
    return {
        "langfuse_session_id": session_id,
        "langfuse_tags": [f"channel:{channel}"],
    }


def build_callbacks(
    settings: Settings,
    *,
    session_id: str,
    channel: str,
) -> list[BaseCallbackHandler]:
    """Return LangChain callbacks for a chat turn."""
    del session_id, channel
    if not settings.langfuse_enabled:
        return []

    if _langfuse_client is None and not init_langfuse(settings):
        return []

    try:
        from langfuse.langchain import CallbackHandler
    except ImportError:
        logger.warning("Langfuse LangChain integration is not available")
        return []

    try:
        return [CallbackHandler()]
    except Exception:
        logger.warning("Failed to create Langfuse callback handler", exc_info=True)
        return []
