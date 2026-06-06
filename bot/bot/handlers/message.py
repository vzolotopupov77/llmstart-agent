"""Handler for user text messages."""

import logging

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message

from bot.api.core_client import CoreClient, CoreClientError
from bot.services.session_store import SessionStore
from bot.utils.messaging import deliver_chat_response

logger = logging.getLogger(__name__)

NON_TEXT_REPLY = "Пока я понимаю только текстовые сообщения. Напишите вопрос текстом."


def create_message_router(core_client: CoreClient, session_store: SessionStore) -> Router:
    """Build router for chat messages proxied to Core."""
    router = Router()

    @router.message(F.text)
    async def handle_text(message: Message) -> None:
        if message.chat is None or message.text is None:
            return

        chat_id = message.chat.id
        session_id = session_store.get(chat_id)
        text = message.text.strip()
        if not text or message.bot is None:
            return

        await message.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        try:
            response = await core_client.chat(message=text, session_id=session_id)
        except CoreClientError as exc:
            logger.warning(
                "Core chat failed: chat_id=%s session_id=%s error=%s",
                chat_id,
                session_id,
                type(exc).__name__,
            )
            if "Сессия устарела" in exc.user_message or "недействительна" in exc.user_message:
                session_store.clear(chat_id)
            await message.answer(exc.user_message)
            return

        session_store.set(chat_id, response.session_id)
        logger.info(
            "Chat turn ok: chat_id=%s session_id=%s status=200",
            chat_id,
            response.session_id,
        )
        await deliver_chat_response(message, response)

    @router.message()
    async def handle_non_text(message: Message) -> None:
        await message.answer(NON_TEXT_REPLY)

    return router
