"""Telegram message delivery helpers."""

import re

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.api.core_client import ChatResponse, ProductItem
from bot.utils.price import format_price

TELEGRAM_MAX_MESSAGE_LENGTH = 4096
CHUNK_SIZE = 4000


async def deliver_chat_response(message: Message, response: ChatResponse) -> None:
    """Send Core response to user with HTML fallback and payment link."""
    html = response.message_html
    plain = response.message
    if response.products:
        block_plain, block_html = _format_products_block(response.products)
        if block_plain and not _block_already_present(plain, block_plain):
            plain = f"{plain.rstrip()}\n\n{block_plain}"
            html = f"{html.rstrip()}\n\n{block_html}"
    await _send_html_or_plain(message, html, plain)

    if response.payment_link and response.payment_link not in response.message_html:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Перейти к оплате",
                        url=response.payment_link,
                    ),
                ],
            ],
        )
        await message.answer("Ссылка на оплату:", reply_markup=keyboard)


async def send_long_text(message: Message, text: str, *, parse_mode: str | None = None) -> None:
    """Split and send text longer than Telegram limit."""
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        await message.answer(text, parse_mode=parse_mode)
        return

    chunks = _split_text(text, CHUNK_SIZE)
    for chunk in chunks:
        await message.answer(chunk, parse_mode=parse_mode)


async def _send_html_or_plain(message: Message, html: str, plain: str) -> None:
    try:
        await send_long_text(message, html, parse_mode="HTML")
    except TelegramBadRequest:
        await send_long_text(message, _plain_without_markdown(plain))


def _format_products_block(products: list[ProductItem]) -> tuple[str, str]:
    lines_plain: list[str] = ["Курсы:"]
    lines_html: list[str] = ["<b>Курсы:</b>"]
    for product in products:
        price = format_price(product.price, product.currency)
        lines_plain.append(f"• {product.title} — {price}")
        lines_html.append(f"• {product.title} — {price}")
    plain = "\n".join(lines_plain)
    html = "\n".join(lines_html)
    return plain, html


def _block_already_present(message: str, block_plain: str) -> bool:
    first_line = block_plain.splitlines()[0]
    if first_line in message:
        return True
    return any(line in message for line in block_plain.splitlines()[1:])


def _plain_without_markdown(text: str) -> str:
    """Strip common markdown when HTML delivery fails."""
    without_bold = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", without_bold)


def _split_text(text: str, max_len: int) -> list[str]:
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, max_len)
        if split_at < max_len // 2:
            split_at = remaining.rfind("\n", 0, max_len)
        if split_at < max_len // 2:
            split_at = max_len
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    return [chunk for chunk in chunks if chunk]
