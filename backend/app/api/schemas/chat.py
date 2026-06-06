"""Pydantic schemas for POST /api/v1/chat."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.api.schemas.product import ProductItem


class ChatRequest(BaseModel):
    """Incoming chat turn."""

    message: str = Field(..., min_length=1, max_length=4000)
    session_id: UUID | None = None
    channel: Literal["web", "telegram"]

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "message must not be empty"
            raise ValueError(msg)
        return stripped


class ToolStatusItem(BaseModel):
    """Tool invocation status for JSON response."""

    name: str
    status: Literal["done", "error"]
    title: str


class ChatResponse(BaseModel):
    """JSON response for a completed chat turn."""

    session_id: UUID
    channel: Literal["web", "telegram"]
    message: str
    message_html: str
    reasoning: str
    tools: list[ToolStatusItem]
    products: list[ProductItem] | None = None
    payment_link: str | None = None
