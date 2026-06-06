"""Shared pytest fixtures."""

import os

os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from mcp.types import Tool

from app.agent.react_runner import ToolCallRecord, TurnResult
from app.core.config import Settings, get_settings
from app.factory import create_app
from app.mcp_client.runtime import apply_mcp_server_env


class FakeMcpClient:
    """In-memory MCP client for API tests."""

    def __init__(self) -> None:
        self.is_connected = True

    async def connect(self, settings: Settings) -> None:
        self.is_connected = True

    async def close(self) -> None:
        self.is_connected = False

    async def list_tools(self) -> list[Tool]:
        return [
            Tool(name="search_knowledge_base", description="RAG", inputSchema={"type": "object"}),
            Tool(name="list_b2c_products", description="Catalog", inputSchema={"type": "object"}),
            Tool(
                name="create_payment_link",
                description="Payment",
                inputSchema={"type": "object"},
            ),
            Tool(name="confirm_payment", description="Confirm", inputSchema={"type": "object"}),
            Tool(name="save_lead", description="Lead", inputSchema={"type": "object"}),
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "list_b2c_products":
            return {
                "items": [
                    {
                        "code": "agents",
                        "title": "Промпт-инжиниринг: базовый курс",
                        "price": 9900,
                        "currency": "RUB",
                    },
                ],
            }
        if name == "create_payment_link":
            return {"url": "https://pay.mock.llmstart.ru/checkout?product_id=agents"}
        if name == "search_knowledge_base":
            return [{"text": "chunk", "source": "faq.md", "segment": arguments.get("segment")}]
        if name == "confirm_payment":
            return {"status": "confirmed"}
        if name == "save_lead":
            return {"ok": True}
        return {"ok": True}

    async def health_check(self) -> int:
        return 5


class FakeReactRunner:
    """Scripted agent responses without LLM."""

    def run_turn(
        self,
        history: list[object],
        user_message: str,
        callbacks: list[object] | None = None,
    ) -> TurnResult:
        if "корпоратив" in user_message.lower():
            tools = [
                ToolCallRecord(
                    name="search_knowledge_base",
                    status="done",
                    title="Поиск в базе знаний",
                ),
            ]
            reasoning = "Запрос B2B — поиск в корпоративной базе знаний."
            message = "Мы проводим корпоративное обучение по AI."
        else:
            tools = [
                ToolCallRecord(
                    name="list_b2c_products",
                    status="done",
                    title="Каталог курсов",
                ),
            ]
            reasoning = "Подбор курса для новичка из каталога."
            message = "Рекомендую курс agents для новичка."

        return TurnResult(
            new_messages=[AIMessage(content=message)],
            final_message=message,
            reasoning=reasoning,
            tools=tools,
            products=[
                {
                    "code": "agents",
                    "title": "Промпт-инжиниринг: базовый курс",
                    "price": 9900,
                    "currency": "RUB",
                },
            ],
            payment_link=None,
        )


@pytest.fixture
def test_app() -> Generator[Any, None, None]:
    get_settings.cache_clear()
    apply_mcp_server_env(get_settings())
    app = create_app(
        mcp_client=FakeMcpClient(),  # type: ignore[arg-type]
        react_runner=FakeReactRunner(),  # type: ignore[arg-type]
    )
    yield app
    get_settings.cache_clear()


@pytest.fixture
def client(test_app: Any) -> Generator[TestClient, None, None]:
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def session_id(client: TestClient) -> str:
    response = client.post(
        "/api/v1/chat",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"message": "Привет", "channel": "web"},
    )
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    session_value = body["session_id"]
    assert isinstance(session_value, str)
    return session_value
