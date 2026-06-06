"""Telegram bot entry point (long polling)."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher

from bot.api.core_client import CoreClient
from bot.config import get_settings
from bot.handlers.message import create_message_router
from bot.handlers.start import create_start_router
from bot.services.session_store import SessionStore


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )


async def run_bot() -> None:
    """Start long polling."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    core_client = CoreClient(settings)
    session_store = SessionStore()

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(create_start_router(session_store))
    dispatcher.include_router(create_message_router(core_client, session_store))

    logging.getLogger(__name__).info(
        "Starting Telegram bot (backend=%s)",
        settings.backend_base_url,
    )
    await dispatcher.start_polling(bot)


def main() -> None:
    """CLI entry."""
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
