"""LangChain callbacks for SSE tool events."""

from collections.abc import Callable
from typing import Any, Literal
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler

from app.mcp_client.tool_adapter import get_tool_title

ToolEventCallback = Callable[[str, Literal["started", "done", "error"], str], None]


class ToolEventCollector(BaseCallbackHandler):
    """Collect tool start/end events for SSE streaming."""

    def __init__(self, on_event: ToolEventCallback | None = None) -> None:
        self.events: list[tuple[str, str, str]] = []
        self._run_tool_names: dict[UUID, str] = {}
        self._on_event = on_event

    def _emit(self, name: str, status: Literal["started", "done", "error"], title: str) -> None:
        self.events.append((name, status, title))
        if self._on_event is not None:
            self._on_event(name, status, title)

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name", "unknown")
        if not isinstance(name, str):
            name = "unknown"
        self._run_tool_names[run_id] = name
        self._emit(name, "started", get_tool_title(name))

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = self._run_tool_names.get(run_id, "unknown")
        self._emit(name, "done", get_tool_title(name))

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        name = self._run_tool_names.get(run_id, "unknown")
        self._emit(name, "error", get_tool_title(name))
