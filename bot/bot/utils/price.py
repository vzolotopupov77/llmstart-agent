"""Price formatting for Telegram product blocks."""


def format_price(amount_kopecks: int, currency: str) -> str:
    """Format minor units as human-readable price (same rule as web widget)."""
    major = round(amount_kopecks / 100)
    formatted = f"{major:,}".replace(",", " ")
    symbol = "₽" if currency == "RUB" else currency
    return f"{formatted} {symbol}"
