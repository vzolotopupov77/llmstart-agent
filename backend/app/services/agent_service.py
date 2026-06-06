"""Orchestrates agent turns and maps results to API models."""

import queue
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from langchain_core.messages import HumanMessage

from app.agent.react_runner import ReactRunner, ToolCallRecord, TurnResult
from app.agent.streaming_callbacks import ToolEventCollector
from app.api.schemas.chat import ChatResponse, ToolStatusItem
from app.api.schemas.product import ProductItem
from app.api.schemas.sse import (
    SseDoneData,
    SseMessageData,
    SsePaymentLinkData,
    SseProductsData,
    SseReasoningData,
    SseToolData,
)
from app.core.config import Settings
from app.core.exceptions import McpUnavailableError
from app.mcp_client.context import TurnContext, clear_turn_context, set_turn_context
from app.observability.langfuse import (
    build_callbacks,
    build_langfuse_metadata,
    flush_callbacks,
)
from app.services.channel_formatter import format_message
from app.services.message_chunker import chunk_message
from app.services.price_formatter import normalize_kopeck_prices_in_text
from app.services.session_store import Session, SessionStore
from app.services.sse_formatter import format_sse_event
from app.services.sse_pacing import (
    SSE_MESSAGE_CHUNK_DELAY_SECONDS,
    SSE_POST_STEP_DELAY_SECONDS,
    SSE_TOOL_STEP_DELAY_SECONDS,
)

_STREAM_SENTINEL = object()


class AgentService:
    """High-level chat orchestration."""

    def __init__(
        self,
        session_store: SessionStore,
        react_runner: ReactRunner,
        tools_ready: bool,
        settings: Settings,
    ) -> None:
        self._session_store = session_store
        self._react_runner = react_runner
        self._tools_ready = tools_ready
        self._settings = settings

    def run_chat_turn(
        self,
        *,
        message: str,
        session_id: UUID | None,
        channel: str,
    ) -> ChatResponse:
        """Process one chat turn and return JSON response."""
        session, turn, _tool_collector = self._execute_turn(
            message=message,
            session_id=session_id,
            channel=channel,
        )

        products = _map_products(turn.products)
        plain = turn.final_message.strip()
        if channel == "telegram":
            plain = normalize_kopeck_prices_in_text(plain, products)
        plain, html = format_message(channel, plain)

        return ChatResponse(
            session_id=session.id,
            channel=channel,
            message=plain,
            message_html=html,
            reasoning=turn.reasoning,
            tools=[
                ToolStatusItem(
                    name=tool.name,
                    status="done" if tool.status == "done" else "error",
                    title=tool.title,
                )
                for tool in turn.tools
            ],
            products=products,
            payment_link=turn.payment_link,
        )

    def iter_chat_turn_stream(
        self,
        *,
        message: str,
        session_id: UUID | None,
        channel: str,
    ) -> Iterator[str]:
        """Stream SSE events during the turn, not only after agent completion."""
        if not self._tools_ready:
            raise McpUnavailableError(McpUnavailableError.DEFAULT_MESSAGE)

        session, _created = self._session_store.get_or_create(session_id, channel)
        self._session_store.touch(session)

        return self._generate_chat_turn_stream(
            message=message,
            channel=channel,
            session=session,
        )

    def _generate_chat_turn_stream(
        self,
        *,
        message: str,
        channel: str,
        session: Session,
    ) -> Iterator[str]:
        event_queue: queue.Queue[str | object] = queue.Queue()
        holder = _StreamTurnHolder()
        live_streamed: set[tuple[str, str]] = set()

        def on_tool_event(
            name: str,
            status: Literal["started", "done", "error"],
            title: str,
        ) -> None:
            live_streamed.add((name, status))
            event_queue.put(
                format_sse_event(
                    "tool",
                    SseToolData(
                        name=name,
                        status=status,
                        title=title,
                    ),
                ),
            )

        def execute_turn() -> None:
            tool_collector = ToolEventCollector(on_event=on_tool_event)
            set_turn_context(TurnContext(session_id=str(session.id), channel=channel))
            try:
                callbacks = build_callbacks(
                    self._settings,
                    session_id=str(session.id),
                    channel=channel,
                )
                turn = self._react_runner.run_turn(
                    history=list(session.messages),
                    user_message=message,
                    callbacks=[*callbacks, tool_collector],
                    metadata=build_langfuse_metadata(
                        session_id=str(session.id),
                        channel=channel,
                    ),
                )
                flush_callbacks(callbacks)
                session.messages.append(HumanMessage(content=message))
                session.messages.extend(turn.new_messages)
                holder.turn = turn
                holder.tool_collector = tool_collector
            except Exception as exc:  # noqa: BLE001
                holder.error = exc
            finally:
                clear_turn_context()
                event_queue.put(_STREAM_SENTINEL)

        yield format_sse_event(
            "reasoning",
            SseReasoningData(text="Анализ запроса пользователя."),
        )

        worker = threading.Thread(target=execute_turn, daemon=True)
        worker.start()

        while True:
            queued = event_queue.get()
            if queued is _STREAM_SENTINEL:
                break
            yield str(queued)

        worker.join()

        if holder.error is not None:
            raise holder.error

        turn = holder.turn
        if turn is None:
            raise RuntimeError("Agent turn completed without a result")

        for name, status, title in _resolve_tool_events(holder.tool_collector, turn.tools):
            if (name, status) in live_streamed:
                continue
            yield format_sse_event(
                "tool",
                SseToolData(
                    name=name,
                    status=status,
                    title=title,
                ),
            )
            time.sleep(SSE_TOOL_STEP_DELAY_SECONDS)

        yield from _iter_tail_sse_events(turn=turn, session_id=session.id)

    def _execute_turn(
        self,
        *,
        message: str,
        session_id: UUID | None,
        channel: str,
        collect_tool_events: bool = False,
    ) -> tuple[Session, TurnResult, ToolEventCollector | None]:
        if not self._tools_ready:
            raise McpUnavailableError(McpUnavailableError.DEFAULT_MESSAGE)

        session, _created = self._session_store.get_or_create(session_id, channel)
        self._session_store.touch(session)

        tool_collector = ToolEventCollector() if collect_tool_events else None
        set_turn_context(TurnContext(session_id=str(session.id), channel=channel))
        try:
            callbacks = build_callbacks(
                self._settings,
                session_id=str(session.id),
                channel=channel,
            )
            if tool_collector is not None:
                callbacks = [*callbacks, tool_collector]

            turn = self._react_runner.run_turn(
                history=list(session.messages),
                user_message=message,
                callbacks=callbacks,
                metadata=build_langfuse_metadata(
                    session_id=str(session.id),
                    channel=channel,
                ),
            )
            flush_callbacks(callbacks)
        finally:
            clear_turn_context()

        session.messages.append(HumanMessage(content=message))
        session.messages.extend(turn.new_messages)

        return session, turn, tool_collector


def _map_products(items: list[dict[str, str | int]] | None) -> list[ProductItem] | None:
    if not items:
        return None
    mapped: list[ProductItem] = []
    for item in items:
        code = item.get("code")
        title = item.get("title")
        price = item.get("price")
        currency = item.get("currency")
        if not isinstance(code, str) or not isinstance(title, str):
            continue
        if not isinstance(price, int) or not isinstance(currency, str):
            continue
        mapped.append(
            ProductItem(code=code, title=title, price=price, currency=currency),
        )
    return mapped or None


@dataclass
class _StreamTurnHolder:
    turn: TurnResult | None = None
    tool_collector: ToolEventCollector | None = None
    error: Exception | None = None


def _iter_tail_sse_events(*, turn: TurnResult, session_id: UUID) -> Iterator[str]:
    products = _map_products(turn.products)
    if products:
        yield format_sse_event(
            "products",
            SseProductsData(items=products),
        )
        time.sleep(SSE_POST_STEP_DELAY_SECONDS)

    for delta in chunk_message(turn.final_message):
        yield format_sse_event("message", SseMessageData(delta=delta))
        time.sleep(SSE_MESSAGE_CHUNK_DELAY_SECONDS)

    if turn.payment_link:
        yield format_sse_event(
            "payment_link",
            SsePaymentLinkData(url=turn.payment_link),
        )
        time.sleep(SSE_POST_STEP_DELAY_SECONDS)

    yield format_sse_event(
        "done",
        SseDoneData(session_id=session_id, message=turn.final_message),
    )


def _resolve_tool_events(
    tool_collector: ToolEventCollector | None,
    tools: list[ToolCallRecord],
) -> list[tuple[str, Literal["started", "done", "error"], str]]:
    if tool_collector and tool_collector.events:
        return [
            (name, status, title)  # type: ignore[misc]
            for name, status, title in tool_collector.events
            if status in {"started", "done", "error"}
        ]

    synthesized: list[tuple[str, Literal["started", "done", "error"], str]] = []
    for tool in tools:
        synthesized.append((tool.name, "started", tool.title))
        final_status: Literal["done", "error"] = "done" if tool.status == "done" else "error"
        synthesized.append((tool.name, final_status, tool.title))
    return synthesized
