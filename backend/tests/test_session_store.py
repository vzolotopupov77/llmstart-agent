"""Unit tests for session store."""

from datetime import UTC, datetime, timedelta

from app.services.session_store import SessionStore


def test_get_or_create_new_session() -> None:
    """Creates a new session when session_id is omitted."""
    store = SessionStore(ttl_hours=24)
    session, created = store.get_or_create(None, "web")

    assert created is True
    assert session.channel == "web"


def test_get_or_create_existing_session() -> None:
    """Returns existing session for known session_id."""
    store = SessionStore(ttl_hours=24)
    session, _ = store.get_or_create(None, "web")

    loaded, created = store.get_or_create(session.id, "web")

    assert created is False
    assert loaded.id == session.id


def test_expired_session_returns_none() -> None:
    """Expired sessions are purged on access."""
    store = SessionStore(ttl_hours=1)
    session, _ = store.get_or_create(None, "web")
    session.last_active_at = datetime.now(UTC) - timedelta(hours=2)

    assert store.get(session.id) is None
