"""SSE event serialization for POST /api/v1/chat."""

import json
from collections.abc import Iterable, Iterator

from pydantic import BaseModel


def format_sse_event(event_type: str, data: BaseModel) -> str:
    """Serialize one SSE event block."""
    payload = json.dumps(data.model_dump(mode="json"), ensure_ascii=False)
    return f"event: {event_type}\ndata: {payload}\n\n"


def stream_events(events: Iterable[tuple[str, BaseModel]]) -> Iterator[str]:
    """Yield formatted SSE strings from (event_type, data) pairs."""
    for event_type, data in events:
        yield format_sse_event(event_type, data)
