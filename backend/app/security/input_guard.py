"""Narrow input denylist (FIX-1)."""

from __future__ import annotations

import re

_HACKED_PREFIX = re.compile(r"HACKED\s*:", re.IGNORECASE)
_ROLE_WRAPPERS = (
    re.compile(r"^\s*<system\b", re.IGNORECASE),
    re.compile(r"^\s*System\s*:", re.IGNORECASE),
    re.compile(r"^\s*\[SYSTEM\]", re.IGNORECASE),
)
_MEDICAL_FORMAT = re.compile(
    r"Диагноз\s*:.*Назначение\s*:",
    re.IGNORECASE | re.DOTALL,
)


def input_should_block(message: str, *, security_enabled: bool) -> bool:
    """Return True when the user message matches a high-precision attack template."""
    if not security_enabled:
        return False
    stripped = message.strip()
    if not stripped:
        return False
    if _HACKED_PREFIX.search(stripped):
        return True
    if any(pattern.search(stripped) for pattern in _ROLE_WRAPPERS):
        return True
    return bool(_MEDICAL_FORMAT.search(stripped))
