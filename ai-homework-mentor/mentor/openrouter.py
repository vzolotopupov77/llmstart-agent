"""Health-check и фабрика LLM-клиента OpenRouter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx
from langchain_openrouter import ChatOpenRouter

if TYPE_CHECKING:
    from mentor.config import AppConfig

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_HEALTHCHECK_TIMEOUT = 15.0
DEFAULT_LLM_REQUEST_TIMEOUT = 600


def _normalize_openrouter_model(model: str) -> str:
    clean = model.strip()
    if clean.startswith("openrouter:"):
        return clean.removeprefix("openrouter:")
    return clean


def build_chat_model(config: AppConfig) -> ChatOpenRouter:
    """ChatOpenRouter с таймаутом из конфига (request_timeout — миллисекунды)."""
    timeout_ms = config.llm_request_timeout * 1000
    return ChatOpenRouter(
        model_name=_normalize_openrouter_model(config.model),
        request_timeout=timeout_ms,
    )


def _extract_error_message(response: httpx.Response) -> str:
    try:
        payload: dict[str, Any] = response.json()
    except json.JSONDecodeError:
        return response.text or f"HTTP {response.status_code}"
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str):
            return message
    return response.text or f"HTTP {response.status_code}"


def check_openrouter_connection(
    api_key: str,
    model: str,
    *,
    timeout: float = DEFAULT_HEALTHCHECK_TIMEOUT,
) -> tuple[bool, str]:
    """Минимальный запрос к OpenRouter; возвращает (успех, сообщение)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(OPENROUTER_URL, headers=headers, json=body)
    except httpx.TimeoutException:
        return False, "timeout: OpenRouter не ответил вовремя"
    except httpx.RequestError as exc:
        return False, f"сетевая ошибка: {exc}"

    if response.status_code == httpx.codes.OK:
        return True, "соединение установлено"

    return False, _extract_error_message(response)
