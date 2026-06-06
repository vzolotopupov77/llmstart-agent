"""Integration tests for POST /api/v1/chat."""

from uuid import uuid4


def test_chat_json_returns_contract_fields(client: object) -> None:
    """POST /chat returns JSON contract fields."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"message": "Какой курс новичку?", "channel": "web"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "session_id" in body
    assert body["channel"] == "web"
    assert body["message"]
    assert body["reasoning"]
    assert isinstance(body["tools"], list)
    assert len(body["tools"]) >= 1


def test_chat_creates_and_reuses_session(client: object, session_id: str) -> None:
    """Session persists across turns when session_id is reused."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "message": "Продолжаем диалог",
            "session_id": session_id,
            "channel": "web",
        },
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id


def test_chat_unknown_session_returns_400(client: object) -> None:
    """Unknown session_id returns 400."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={
            "message": "Привет",
            "session_id": str(uuid4()),
            "channel": "web",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Session not found or expired"


def test_chat_telegram_returns_message_html(client: object) -> None:
    """Telegram channel includes message_html."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"message": "Привет", "channel": "telegram"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message_html"]


def test_chat_b2b_uses_knowledge_search(client: object) -> None:
    """B2B-style query triggers knowledge base tool."""
    response = client.post(  # type: ignore[attr-defined]
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"message": "Нужно корпоративное обучение", "channel": "web"},
    )

    assert response.status_code == 200
    tools = [item["name"] for item in response.json()["tools"]]
    assert "search_knowledge_base" in tools


def test_ready_returns_ok(client: object) -> None:
    """GET /ready reports MCP readiness."""
    response = client.get("/ready")  # type: ignore[attr-defined]
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["mcp_tools"] == 5
