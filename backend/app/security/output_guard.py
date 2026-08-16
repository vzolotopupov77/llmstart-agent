"""Output denylist for PROTECTED leaks and false payment claims (FIX-2)."""

from __future__ import annotations

import re

from mcp_server.data_access.payments import has_confirmed_payment

from app.core.config import Settings
from app.security.constants import (
    INTERNAL_DISCLOSURE_PREFIX,
    PROTECTED_TOOL_NAMES,
    SECURITY_BLOCKED_MARKER,
)

_HACKED_START = re.compile(r"^\s*HACKED\s*:", re.IGNORECASE)
_URLS = re.compile(r"https?://\S+", re.IGNORECASE)
_PARAM_NAMES = re.compile(r"\b(?:session_id|product_id)\b")
_PAYMENT_CONFIRMED = re.compile(
    r"(оплат\w*\s+(?:подтвержд\w+|зачисл\w+|принят\w+)|курс\s+оплачен|доступ\s+открыт)",
    re.IGNORECASE,
)


def apply_output_guard(message: str, *, session_id: str, settings: Settings) -> str:
    """Replace leaking/false-payment text with the block marker when guards are on."""
    if not settings.security_enabled:
        return message
    if _should_block(
        message,
        session_id=session_id,
        canary_token=settings.security_canary_token,
    ):
        return SECURITY_BLOCKED_MARKER
    return message


def _should_block(message: str, *, session_id: str, canary_token: str) -> bool:
    if canary_token and canary_token in message:
        return True
    if INTERNAL_DISCLOSURE_PREFIX in message:
        return True
    if _HACKED_START.search(message):
        return True
    lowered = message
    for name in PROTECTED_TOOL_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", lowered):
            return True
    if _PARAM_NAMES.search(_URLS.sub(" ", message)):
        return True
    return bool(_PAYMENT_CONFIRMED.search(message) and not has_confirmed_payment(session_id))
