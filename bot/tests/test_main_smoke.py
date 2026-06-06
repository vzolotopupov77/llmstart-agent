"""Smoke tests for bot startup wiring."""

from aiogram import Dispatcher

from bot.api.core_client import CoreClient
from bot.config import Settings
from bot.handlers.message import create_message_router
from bot.handlers.start import create_start_router
from bot.services.session_store import SessionStore


def test_dispatcher_wiring(settings: Settings) -> None:
    session_store = SessionStore()
    core_client = CoreClient(settings)
    dispatcher = Dispatcher()
    dispatcher.include_router(create_start_router(session_store))
    dispatcher.include_router(create_message_router(core_client, session_store))
    assert len(dispatcher.sub_routers) == 2
