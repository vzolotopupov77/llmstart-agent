"""Tests for in-memory session store."""

from uuid import uuid4

from bot.services.session_store import SessionStore


def test_set_and_get_session() -> None:
    store = SessionStore()
    session_id = str(uuid4())
    store.set(42, session_id)
    assert store.get(42) == session_id


def test_clear_session() -> None:
    store = SessionStore()
    store.set(1, str(uuid4()))
    store.clear(1)
    assert store.get(1) is None


def test_get_missing_returns_none() -> None:
    store = SessionStore()
    assert store.get(999) is None
