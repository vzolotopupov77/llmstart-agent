"""Schemas for GET /ready."""

from pydantic import BaseModel


class ReadyResponse(BaseModel):
    """Readiness probe response."""

    status: str
    mcp_tools: int
