"""Format agent messages per channel."""

import re
from html import escape
from html.parser import HTMLParser

import markdown

MARKDOWN_EXTENSIONS = ["nl2br", "sane_lists"]


def format_message(channel: str, message: str) -> tuple[str, str]:
    """Return plain message and HTML representation."""
    plain = message.strip()
    if channel == "telegram":
        html = to_telegram_html(plain)
        return plain, html
    return plain, plain


def to_telegram_html(text: str) -> str:
    """Convert markdown-ish text to Telegram-compatible HTML."""
    rendered = markdown.markdown(text, extensions=MARKDOWN_EXTENSIONS)
    telegram_html = _html_to_telegram_html(rendered)
    if telegram_html:
        return telegram_html
    escaped = escape(text.strip())
    return escaped or "…"


def _html_to_telegram_html(html: str) -> str:
    parser = _TelegramHTMLParser()
    parser.feed(html)
    parser.close()
    return re.sub(r"\n{3,}", "\n\n", parser.result.strip())


class _TelegramHTMLParser(HTMLParser):
    """Map intermediate HTML to tags supported by Telegram parse_mode=HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._list_stack: list[str] = []
        self._ol_index = 0

    @property
    def result(self) -> str:
        return "".join(self._parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"b", "strong"}:
            self._parts.append("<b>")
            return
        if tag in {"i", "em"}:
            self._parts.append("<i>")
            return
        if tag == "a":
            href = _attr_value(attrs, "href")
            if href:
                self._parts.append(f'<a href="{escape(href, quote=True)}">')
            return
        if tag == "code":
            self._parts.append("<code>")
            return
        if tag == "pre":
            self._parts.append("<pre>")
            return
        if tag == "blockquote":
            self._parts.append("<blockquote>")
            return
        if tag == "br":
            self._append_newline()
            return
        if tag == "p":
            self._ensure_newline_before_block()
            return
        if tag == "ol":
            self._list_stack.append("ol")
            self._ol_index = 0
            return
        if tag == "ul":
            self._list_stack.append("ul")
            return
        if tag == "li":
            self._ensure_newline_before_block()
            if self._list_stack and self._list_stack[-1] == "ol":
                self._ol_index += 1
                self._parts.append(f"{self._ol_index}. ")
            else:
                self._parts.append("• ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"b", "strong"}:
            self._parts.append("</b>")
            return
        if tag in {"i", "em"}:
            self._parts.append("</i>")
            return
        if tag == "a":
            self._parts.append("</a>")
            return
        if tag == "code":
            self._parts.append("</code>")
            return
        if tag == "pre":
            self._parts.append("</pre>")
            return
        if tag == "blockquote":
            self._parts.append("</blockquote>")
            return
        if tag == "p":
            self._append_newline()
            return
        if tag in {"ol", "ul"}:
            if self._list_stack:
                self._list_stack.pop()
            self._append_newline()

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(escape(data))

    def _ensure_newline_before_block(self) -> None:
        if self._parts and not self._parts[-1].endswith("\n"):
            self._append_newline()

    def _append_newline(self) -> None:
        if self._parts and self._parts[-1].endswith("\n"):
            return
        self._parts.append("\n")


def _attr_value(attrs: list[tuple[str, str | None]], name: str) -> str | None:
    for key, value in attrs:
        if key.lower() == name and value:
            return value
    return None
