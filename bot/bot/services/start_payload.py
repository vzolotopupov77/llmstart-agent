"""Parse /start deep-link payload for web handoff."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

SESSION_PREFIX = "s_"


@dataclass(frozen=True, slots=True)
class StartPayloadResult:
    """Result of parsing Telegram /start argument."""

    kind: Literal["empty", "handoff", "invalid"]
    session_id: UUID | None = None


def parse_start_payload(payload: str | None) -> StartPayloadResult:
    """Parse deep link payload `s_<uuid>` from /start command."""
    if payload is None:
        return StartPayloadResult(kind="empty")

    trimmed = payload.strip()
    if not trimmed:
        return StartPayloadResult(kind="empty")

    if not trimmed.startswith(SESSION_PREFIX):
        return StartPayloadResult(kind="invalid")

    uuid_part = trimmed[len(SESSION_PREFIX) :]
    if not uuid_part:
        return StartPayloadResult(kind="invalid")

    try:
        session_id = UUID(uuid_part)
    except ValueError:
        return StartPayloadResult(kind="invalid")

    return StartPayloadResult(kind="handoff", session_id=session_id)
