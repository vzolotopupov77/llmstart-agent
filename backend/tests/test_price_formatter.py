"""Tests for price normalization in telegram messages."""

from app.api.schemas.product import ProductItem
from app.services.price_formatter import normalize_kopeck_prices_in_text


def test_normalize_known_product_price() -> None:
    products = [
        ProductItem(
            code="agents",
            title="Базовый курс",
            price=3_900_000,
            currency="RUB",
        ),
    ]
    text = "Курс agents стоит 3900000 руб."
    result = normalize_kopeck_prices_in_text(text, products)
    assert "39 000 ₽" in result
    assert "3900000" not in result


def test_normalize_large_literal_without_products() -> None:
    text = "Стоимость: 5900000"
    result = normalize_kopeck_prices_in_text(text, None)
    assert "59 000 ₽" in result
