"""SSE event payload schemas for POST /api/v1/chat streaming."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.api.schemas.product import ProductItem


class SseReasoningData(BaseModel):
    """Payload for event: reasoning."""

    text: str


class SseToolData(BaseModel):
    """Payload for event: tool."""

    name: str
    status: Literal["started", "done", "error"]
    title: str


class SseProductsData(BaseModel):
    """Payload for event: products."""

    items: list[ProductItem]


class SseMessageData(BaseModel):
    """Payload for event: message."""

    delta: str


class SsePaymentLinkData(BaseModel):
    """Payload for event: payment_link."""

    url: str


class SseDoneData(BaseModel):
    """Payload for event: done."""

    session_id: UUID
    message: str


class SseErrorData(BaseModel):
    """Payload for event: error."""

    detail: str
