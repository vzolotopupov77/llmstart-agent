"""Format and normalize product prices in user-facing text."""

import re

from app.api.schemas.product import ProductItem

# Smallest catalog price in kopecks (consultation 15 000 ₽).
_MIN_KOPECKS_LITERAL = 1_500_000


def format_price_display(amount_kopecks: int, currency: str) -> str:
    """Format minor units as human-readable price (RUB: kopecks → rubles)."""
    major = round(amount_kopecks / 100)
    formatted = f"{major:,}".replace(",", " ")
    if currency == "RUB":
        return f"{formatted} ₽"
    return f"{formatted} {currency}"


def normalize_kopeck_prices_in_text(
    text: str,
    products: list[ProductItem] | None = None,
) -> str:
    """Replace raw kopeck literals with formatted ruble prices."""
    result = text
    known_prices: set[int] = set()
    if products:
        known_prices.update(product.price for product in products)

    for kopecks in sorted(known_prices, reverse=True):
        display = format_price_display(kopecks, "RUB")
        result = re.sub(rf"\b{re.escape(str(kopecks))}\b", display, result)

    def repl_large(match: re.Match[str]) -> str:
        value = int(match.group(1))
        if value >= _MIN_KOPECKS_LITERAL:
            return format_price_display(value, "RUB")
        return match.group(0)

    return re.sub(r"\b(\d{6,})\b", repl_large, result)
