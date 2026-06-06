"""In-memory session storage with TTL."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from langchain_core.messages import BaseMessage

from app.core.exceptions import SessionNotFoundError


@dataclass
class Session:
    """Conversation session stored in memory."""

    id: UUID
    channel: str
    messages: list[BaseMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_active_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = field(default_factory=dict)


class SessionStore:
    """In-memory dict of sessions with TTL sweep."""

    def __init__(self, ttl_hours: int = 24) -> None:
        self._sessions: dict[UUID, Session] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, session_id: UUID) -> Session | None:
        """Return session if present and not expired."""
        self._purge_expired()
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if self._is_expired(session):
            del self._sessions[session_id]
            return None
        return session

    def get_or_create(
        self,
        session_id: UUID | None,
        channel: str,
    ) -> tuple[Session, bool]:
        """Return existing or new session. Raises if explicit id is missing."""
        self._purge_expired()
        if session_id is not None:
            session = self.get(session_id)
            if session is None:
                raise SessionNotFoundError
            return session, False

        new_session = Session(id=uuid4(), channel=channel)
        self._sessions[new_session.id] = new_session
        return new_session, True

    def touch(self, session: Session) -> None:
        """Update last activity timestamp."""
        session.last_active_at = datetime.now(UTC)

    def _is_expired(self, session: Session) -> bool:
        return datetime.now(UTC) - session.last_active_at > self._ttl

    def _purge_expired(self) -> None:
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_expired(session)
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
