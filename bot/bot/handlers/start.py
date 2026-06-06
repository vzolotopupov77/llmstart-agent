"""Handler for /start command and web handoff."""

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.services.session_store import SessionStore
from bot.services.start_payload import parse_start_payload

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Здравствуйте! Я ИИ-консультант LLMStart.\n\n"
    "Помогу подобрать курс, ответить на вопросы и оформить покупку.\n"
    "Напишите ваш вопрос текстом."
)

HANDOFF_OK_TEXT = "Продолжаем диалог с сайта. Напишите сообщение — я учту предыдущий контекст."

INVALID_HANDOFF_TEXT = (
    "Ссылка с сайта устарела или некорректна. Напишите вопрос — начнём новый диалог."
)


def create_start_router(session_store: SessionStore) -> Router:
    """Build router for /start with session handoff."""
    router = Router()

    @router.message(CommandStart())
    async def handle_start(message: Message) -> None:
        if message.chat is None:
            return

        chat_id = message.chat.id
        payload = _extract_start_argument(message.text)
        parsed = parse_start_payload(payload)

        if parsed.kind == "handoff" and parsed.session_id is not None:
            session_store.set(chat_id, parsed.session_id)
            logger.info(
                "Handoff session bound: chat_id=%s session_id=%s",
                chat_id,
                parsed.session_id,
            )
            await message.answer(HANDOFF_OK_TEXT)
            return

        if parsed.kind == "invalid":
            session_store.clear(chat_id)
            await message.answer(INVALID_HANDOFF_TEXT)
            return

        await message.answer(WELCOME_TEXT)

    return router


def _extract_start_argument(text: str | None) -> str | None:
    if not text:
        return None
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[1].strip() or None
