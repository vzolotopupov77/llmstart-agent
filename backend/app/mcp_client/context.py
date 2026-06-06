"""Per-turn context injected into MCP tool calls."""

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class TurnContext:
    """Context for the current agent turn."""

    session_id: str
    channel: str


_turn_context: ContextVar[TurnContext | None] = ContextVar("turn_context", default=None)
_active_turn_context: TurnContext | None = None


def set_turn_context(context: TurnContext) -> None:
    """Set turn context for the current scope and LangGraph worker threads."""
    global _active_turn_context
    _active_turn_context = context
    _turn_context.set(context)


def get_turn_context() -> TurnContext:
    """Return turn context or raise if missing."""
    context = _turn_context.get() or _active_turn_context
    if context is None:
        msg = "Turn context is not set"
        raise RuntimeError(msg)
    return context


def clear_turn_context() -> None:
    """Clear turn context."""
    global _active_turn_context
    _active_turn_context = None
    _turn_context.set(None)
