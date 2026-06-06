"""Unit tests for channel formatter."""

from app.services.channel_formatter import format_message, to_telegram_html


def test_telegram_html_escapes_script() -> None:
    """Strips unsafe HTML tags for Telegram."""
    html = to_telegram_html("<script>alert(1)</script>Текст")
    assert "<script>" not in html
    assert "Текст" in html


def test_format_message_web_returns_plain() -> None:
    """Web channel keeps plain text for HTML field."""
    plain, html = format_message("web", "Привет")
    assert plain == "Привет"
    assert html == "Привет"


def test_format_message_telegram_renders_bold() -> None:
    """Telegram channel converts markdown bold to <b>."""
    plain, html = format_message("telegram", "**Жирный** текст")
    assert plain == "**Жирный** текст"
    assert "<b>Жирный</b>" in html
    assert "**" not in html


def test_telegram_html_numbered_list_with_bold() -> None:
    """Numbered course list renders without unsupported <ol>/<li> tags."""
    text = (
        "1. **Базовый курс по ИИ-агентам** (код: agents)\n"
        "2. **Продвинутый курс Deep Agents** (код: deep-agents)"
    )
    html = to_telegram_html(text)
    assert "<ol" not in html
    assert "<li" not in html
    assert "<p" not in html
    assert "<b>Базовый курс по ИИ-агентам</b>" in html
    assert "1." in html
    assert "2." in html


def test_telegram_html_markdown_link() -> None:
    """Markdown links become Telegram <a href> tags."""
    text = "[Оплатить курс](https://pay.mock.llmstart.ru/checkout?x=1)"
    html = to_telegram_html(text)
    assert '<a href="https://pay.mock.llmstart.ru/checkout?x=1">' in html
    assert "Оплатить курс" in html
    assert "[" not in html
