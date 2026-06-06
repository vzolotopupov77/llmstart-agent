"""HTTP client for Agent Core POST /api/v1/chat."""

import asyncio
import logging
from http import HTTPStatus
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel

from bot.config import Settings

logger = logging.getLogger(__name__)

CHAT_PATH = "/api/v1/chat"
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.5


class ProductItem(BaseModel):
    """B2C product card from Core."""

    code: str
    title: str
    price: int
    currency: str


class ChatResponse(BaseModel):
    """Successful JSON response from Core."""

    session_id: UUID
    channel: Literal["web", "telegram"]
    message: str
    message_html: str
    reasoning: str = ""
    products: list[ProductItem] | None = None
    payment_link: str | None = None


class CoreClientError(Exception):
    """Core API error with a user-facing message."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


class CoreClient:
    """Thin async client for Agent Core chat endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._timeout = httpx.Timeout(settings.chat_timeout_seconds)

    async def chat(
        self,
        *,
        message: str,
        session_id: str | UUID | None = None,
    ) -> ChatResponse:
        """Send one chat turn to Core with channel=telegram."""
        payload: dict[str, str] = {
            "message": message,
            "channel": "telegram",
        }
        if session_id is not None:
            payload["session_id"] = str(session_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    base_url=self._settings.backend_base_url,
                    timeout=self._timeout,
                ) as client:
                    response = await client.post(
                        CHAT_PATH,
                        json=payload,
                        headers=headers,
                    )
                return self._parse_response(response)
            except CoreClientError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.TransportError) as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    delay = RETRY_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "Core request failed (attempt %s/%s), retry in %ss: %s",
                        attempt + 1,
                        MAX_RETRIES + 1,
                        delay,
                        type(exc).__name__,
                    )
                    await asyncio.sleep(delay)
                    continue
                msg = "Сервис временно недоступен. Попробуйте позже."
                raise CoreClientError(msg) from exc

        msg = "Сервис временно недоступен. Попробуйте позже."
        raise CoreClientError(msg) from last_error

    def _parse_response(self, response: httpx.Response) -> ChatResponse:
        if response.status_code == HTTPStatus.OK:
            return ChatResponse.model_validate(response.json())

        detail = _extract_detail(response)

        if response.status_code == HTTPStatus.BAD_REQUEST:
            raise CoreClientError(
                detail or "Сессия устарела или недействительна. Начните новый диалог.",
            )
        if response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            raise CoreClientError(detail or "Сервис временно недоступен. Попробуйте позже.")
        if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            validation_msg = "Не удалось обработать сообщение. Попробуйте короче."
            raise CoreClientError(validation_msg)

        logger.error("Unexpected Core response: status=%s", response.status_code)
        generic_msg = "Произошла ошибка. Попробуйте позже."
        raise CoreClientError(generic_msg)


def _extract_detail(response: httpx.Response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    detail = body.get("detail")
    if isinstance(detail, str):
        return detail
    return None
