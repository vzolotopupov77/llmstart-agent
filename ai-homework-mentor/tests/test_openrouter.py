"""Тесты health-check OpenRouter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from mentor.openrouter import check_openrouter_connection


def test_check_openrouter_success() -> None:
    response = MagicMock(spec=httpx.Response)
    response.status_code = httpx.codes.OK

    with patch("mentor.openrouter.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.post.return_value = response
        ok, message = check_openrouter_connection("test-key", "google/gemini-2.5-flash")

    assert ok is True
    assert message == "соединение установлено"


def test_check_openrouter_timeout() -> None:
    with patch("mentor.openrouter.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.post.side_effect = httpx.TimeoutException(
            "timeout",
        )
        ok, message = check_openrouter_connection("test-key", "google/gemini-2.5-flash")

    assert ok is False
    assert "timeout" in message


def test_check_openrouter_api_error() -> None:
    response = MagicMock(spec=httpx.Response)
    response.status_code = 401
    response.json.return_value = {"error": {"message": "Invalid API key"}}
    response.text = "Unauthorized"

    with patch("mentor.openrouter.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.post.return_value = response
        ok, message = check_openrouter_connection("bad-key", "google/gemini-2.5-flash")

    assert ok is False
    assert message == "Invalid API key"
