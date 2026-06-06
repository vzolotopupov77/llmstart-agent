"""Tests for message splitting helper."""

from bot.api.core_client import ProductItem
from bot.utils.messaging import _format_products_block, _plain_without_markdown, _split_text
from bot.utils.price import format_price


def test_split_short_text() -> None:
    assert _split_text("hello", 4000) == ["hello"]


def test_format_price_kopecks_to_rubles() -> None:
    assert format_price(3_900_000, "RUB") == "39 000 ₽"


def test_format_products_block() -> None:
    products = [
        ProductItem(code="agents", title="Базовый курс", price=3_900_000, currency="RUB"),
    ]
    plain, html = _format_products_block(products)
    assert "39 000 ₽" in plain
    assert "<b>Курсы:</b>" in html


def test_plain_without_markdown_strips_bold_and_links() -> None:
    text = "**Курс** и [Оплатить](https://pay.example/1)"
    assert _plain_without_markdown(text) == "Курс и Оплатить (https://pay.example/1)"


def test_split_long_text_by_paragraph() -> None:
    part_a = "a" * 100
    part_b = "b" * 100
    text = f"{part_a}\n\n{part_b}"
    chunks = _split_text(text, 120)
    assert len(chunks) == 2
    assert chunks[0] == part_a
    assert chunks[1] == part_b
