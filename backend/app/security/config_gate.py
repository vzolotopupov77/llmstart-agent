"""Gate public config_id behind an eval header (FIX-5)."""

from __future__ import annotations

import hmac

from app.core.config import Settings


def config_id_is_authorized(
    config_id: str | None,
    header_value: str | None,
    settings: Settings,
) -> bool:
    """Allow config_id only when security is off or the eval key matches."""
    if not config_id:
        return True
    if not settings.security_enabled:
        return True
    expected = settings.eval_access_key.strip()
    provided = (header_value or "").strip()
    if not expected or not provided:
        return False
    return _keys_match(provided, expected)


def _keys_match(provided: str, expected: str) -> bool:
    left = provided.encode("utf-8")
    right = expected.encode("utf-8")
    if len(left) != len(right):
        return False
    return hmac.compare_digest(left, right)
