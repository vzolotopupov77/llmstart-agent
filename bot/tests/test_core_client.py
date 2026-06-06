"""Tests for Agent Core HTTP client."""

from uuid import uuid4

import httpx
import pytest

from bot.api.core_client import CoreClient, CoreClientError
from bot.config import Settings


def _chat_response_json(session_id: str | None = None) -> dict[str, object]:
    sid = session_id or str(uuid4())
    return {
        "session_id": sid,
        "channel": "telegram",
        "message": "Привет!",
        "message_html": "<p>Привет!</p>",
        "reasoning": "greeting",
        "tools": [],
        "products": None,
        "payment_link": None,
    }


class _MockAsyncClient:
    """Minimal httpx.AsyncClient stand-in for tests."""

    def __init__(self, response: httpx.Response, *, assert_session: str | None = None) -> None:
        self._response = response
        self._assert_session = assert_session

    async def __aenter__(self) -> "_MockAsyncClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def post(self, _url: str, **kwargs: object) -> httpx.Response:
        json_body = kwargs.get("json")
        assert isinstance(json_body, dict)
        assert json_body["channel"] == "telegram"
        if self._assert_session is not None:
            assert json_body.get("session_id") == self._assert_session
        return self._response


@pytest.mark.asyncio
async def test_chat_success(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    session_id = str(uuid4())
    response = httpx.Response(200, json=_chat_response_json(session_id))

    def client_factory(**_kwargs: object) -> _MockAsyncClient:
        return _MockAsyncClient(response, assert_session=session_id)

    monkeypatch.setattr("bot.api.core_client.httpx.AsyncClient", client_factory)

    core = CoreClient(settings)
    result = await core.chat(message="Привет", session_id=session_id)
    assert str(result.session_id) == session_id
    assert result.message_html == "<p>Привет!</p>"


@pytest.mark.asyncio
async def test_chat_maps_400(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    response = httpx.Response(400, json={"detail": "Session not found or expired"})

    monkeypatch.setattr(
        "bot.api.core_client.httpx.AsyncClient",
        lambda **_kwargs: _MockAsyncClient(response),
    )

    core = CoreClient(settings)
    with pytest.raises(CoreClientError, match="Session not found"):
        await core.chat(message="test")


@pytest.mark.asyncio
async def test_chat_maps_503(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    response = httpx.Response(503, json={"detail": "LLM service unavailable"})

    monkeypatch.setattr(
        "bot.api.core_client.httpx.AsyncClient",
        lambda **_kwargs: _MockAsyncClient(response),
    )

    core = CoreClient(settings)
    with pytest.raises(CoreClientError, match="LLM service unavailable"):
        await core.chat(message="test")


@pytest.mark.asyncio
async def test_chat_network_error_retries(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    class FailingClient:
        async def __aenter__(self) -> "FailingClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def post(self, *_args: object, **_kwargs: object) -> httpx.Response:
            nonlocal calls
            calls += 1
            msg = "network down"
            raise httpx.ConnectError(msg)

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("bot.api.core_client.httpx.AsyncClient", lambda **_kwargs: FailingClient())
    monkeypatch.setattr("bot.api.core_client.asyncio.sleep", fake_sleep)

    core = CoreClient(settings)
    with pytest.raises(CoreClientError, match="Сервис временно недоступен"):
        await core.chat(message="test")

    assert calls == 3
