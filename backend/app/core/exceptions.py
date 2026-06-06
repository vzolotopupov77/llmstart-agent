"""Application-specific exceptions."""


class AppError(Exception):
    """Base application error."""


class SessionNotFoundError(AppError):
    """Raised when session_id is unknown or expired."""


class McpUnavailableError(AppError):
    """Raised when MCP subprocess is not available."""

    DEFAULT_MESSAGE = "Tools service unavailable"


class LlmUnavailableError(AppError):
    """Raised when the LLM provider is unavailable."""

    DEFAULT_MESSAGE = "LLM service unavailable"


class CatalogUnavailableError(AppError):
    """Raised when B2C catalog cannot be loaded."""

    DEFAULT_MESSAGE = "Catalog unavailable"
