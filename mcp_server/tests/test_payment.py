"""Tests for mock payment tools."""

import re

from mcp_server.tools.payment import handle_confirm_payment, handle_create_payment_link


def test_create_payment_link_format(settings_env: object) -> None:
    result = handle_create_payment_link("agents", "sess-123")
    url = result["url"]
    assert url.startswith("https://pay.mock.llmstart.ru/checkout?")
    assert "product_id=agents" in url
    assert "session_id=sess-123" in url
    assert re.search(r"token=[A-Za-z0-9_-]+", url)


def test_create_payment_link_idempotent(settings_env: object) -> None:
    first = handle_create_payment_link("agents", "sess-abc")
    second = handle_create_payment_link("agents", "sess-abc")
    assert first["url"] == second["url"]


def test_confirm_payment_flow(settings_env: object) -> None:
    handle_create_payment_link("vibe-coding-intensive", "sess-pay-1")
    result = handle_confirm_payment("sess-pay-1", "vibe-coding-intensive")
    assert result == {"status": "confirmed"}
    again = handle_confirm_payment("sess-pay-1", "vibe-coding-intensive")
    assert again == {"status": "confirmed"}


def test_confirm_payment_without_link_fails(settings_env: object) -> None:
    try:
        handle_confirm_payment("missing", "agents")
    except ValueError as exc:
        assert "no pending payment" in str(exc)
    else:
        raise AssertionError("expected ValueError")
