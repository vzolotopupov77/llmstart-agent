"""Tests for /start deep-link payload parsing."""

from uuid import UUID

from bot.services.start_payload import parse_start_payload


def test_parse_empty_payload() -> None:
    result = parse_start_payload(None)
    assert result.kind == "empty"
    assert result.session_id is None


def test_parse_whitespace_payload() -> None:
    result = parse_start_payload("   ")
    assert result.kind == "empty"


def test_parse_valid_handoff() -> None:
    session_id = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    result = parse_start_payload(f"s_{session_id}")
    assert result.kind == "handoff"
    assert result.session_id == session_id


def test_parse_invalid_prefix() -> None:
    result = parse_start_payload("x_a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    assert result.kind == "invalid"


def test_parse_empty_uuid_part() -> None:
    result = parse_start_payload("s_")
    assert result.kind == "invalid"


def test_parse_non_uuid() -> None:
    result = parse_start_payload("s_not-a-uuid")
    assert result.kind == "invalid"
