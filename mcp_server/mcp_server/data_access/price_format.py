"""Format catalog prices for display (kopecks → major currency units)."""


def format_price_display(amount_kopecks: int, currency: str) -> str:
    """Format minor units as human-readable price (RUB: kopecks → rubles)."""
    major = round(amount_kopecks / 100)
    formatted = f"{major:,}".replace(",", " ")
    if currency == "RUB":
        return f"{formatted} ₽"
    return f"{formatted} {currency}"
