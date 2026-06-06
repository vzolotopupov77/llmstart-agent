"""In-memory session_id storage per Telegram chat."""

from uuid import UUID


class SessionStore:
    """Maps Telegram chat_id to Agent Core session_id."""

    def __init__(self) -> None:
        self._sessions: dict[int, str] = {}

    def get(self, chat_id: int) -> str | None:
        """Return stored session_id for chat or None."""
        return self._sessions.get(chat_id)

    def set(self, chat_id: int, session_id: str | UUID) -> None:
        """Persist session_id for chat."""
        self._sessions[chat_id] = str(session_id)

    def clear(self, chat_id: int) -> None:
        """Remove session binding for chat."""
        self._sessions.pop(chat_id, None)
