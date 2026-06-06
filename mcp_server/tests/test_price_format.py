"""Tests for price display formatting."""

from mcp_server.data_access.price_format import format_price_display


def test_format_price_display_rub() -> None:
    assert format_price_display(3_900_000, "RUB") == "39 000 ₽"


def test_format_price_display_usd() -> None:
    assert format_price_display(10_000, "USD") == "100 USD"
