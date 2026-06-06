"""Integration tests for POST /api/v1/chat SSE streaming."""

import json
from uuid import uuid4

from app.api.schemas.sse import SseErrorData
from app.core.config import get_settings
from app.services.sse_formatter import format_sse_event


def parse_sse_events(body: str) -> list[tuple[str, dict[str, object]]]:
    """Parse SSE response body into (event_type, data) pairs."""
    events: list[tuple[str, dict[str, object]]] = []
    current_event: str | None = None

    for line in body.splitlines():
        if line.startswith("event: "):
            current_event = line.removeprefix("event: ")
        elif line.startswith("data: ") and current_event is not None:
            events.append((current_event, json.loads(line.removeprefix("data: "))))
            current_event = None

    return events


def test_chat_sse_returns_stream(client: object) -> None:
    """SSE Accept header returns event stream with contract events."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        json={"message": "Какой курс новичку?", "channel": "web"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers.get("cache-control") == "no-cache"

    events = parse_sse_events(response.text)
    event_types = [event_type for event_type, _ in events]

    assert event_types[0] == "reasoning"
    assert "tool" in event_types
    assert "products" in event_types
    assert "message" in event_types
    assert event_types[-1] == "done"

    tool_events = [data for event_type, data in events if event_type == "tool"]
    assert any(item["status"] == "started" for item in tool_events)
    assert any(item["status"] == "done" for item in tool_events)

    done_data = events[-1][1]
    assert done_data["message"]
    assert done_data["session_id"]


def test_chat_sse_reuses_session(client: object, session_id: str) -> None:
    """SSE turn preserves session_id across requests."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        json={
            "message": "Продолжаем",
            "session_id": session_id,
            "channel": "web",
        },
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    done_data = events[-1][1]
    assert done_data["session_id"] == session_id


def test_chat_sse_unknown_session_returns_400_json(client: object) -> None:
    """Unknown session_id returns JSON error before stream starts."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        json={
            "message": "Привет",
            "session_id": str(uuid4()),
            "channel": "web",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Session not found or expired"


def test_sse_error_event_format() -> None:
    """Error SSE event matches contract."""
    payload = format_sse_event(
        "error",
        SseErrorData(detail="LLM service unavailable"),
    )
    assert payload.startswith("event: error\n")
    assert '"detail": "LLM service unavailable"' in payload


def test_cors_preflight_allows_widget_origin(client: object) -> None:
    """OPTIONS preflight allows local widget origin."""
    widget_origin = get_settings().cors_origins[0]
    response = client.options(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Origin": widget_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, accept",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == widget_origin
