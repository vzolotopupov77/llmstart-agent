"""LangChain ReAct agent runner."""

import json
import logging
from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError

from app.agent.product_filter import filter_recommended_products
from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import Settings
from app.core.exceptions import LlmUnavailableError
from app.mcp_client.tool_adapter import get_tool_title

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """Recorded tool invocation in a turn."""

    name: str
    status: str
    title: str


@dataclass
class TurnResult:
    """Parsed output of one agent turn."""

    new_messages: list[BaseMessage]
    final_message: str
    reasoning: str
    tools: list[ToolCallRecord] = field(default_factory=list)
    products: list[dict[str, str | int]] | None = None
    payment_link: str | None = None


class ReactRunner:
    """Wraps create_agent for a single conversation turn."""

    def __init__(self, settings: Settings, tools: list[BaseTool]) -> None:
        """Initialize ReAct agent with LLM and MCP-backed tools."""
        model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
        )
        self._agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
        )

    def run_turn(
        self,
        history: list[BaseMessage],
        user_message: str,
        callbacks: list[BaseCallbackHandler] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> TurnResult:
        """Execute one user turn and parse agent output."""
        messages = [*history, HumanMessage(content=user_message)]
        run_config: RunnableConfig = {}
        if callbacks:
            run_config["callbacks"] = callbacks
        if metadata:
            run_config["metadata"] = metadata

        try:
            result = self._agent.invoke(  # type: ignore[call-overload]
                {"messages": messages},
                config=run_config,
            )
        except (APIConnectionError, APITimeoutError, APIStatusError) as exc:
            logger.exception("LLM request failed")
            raise LlmUnavailableError(LlmUnavailableError.DEFAULT_MESSAGE) from exc

        output_messages: list[BaseMessage] = result["messages"]
        start_index = len(messages)
        new_messages = output_messages[start_index:]
        return _parse_turn(new_messages)


def _parse_turn(new_messages: list[BaseMessage]) -> TurnResult:
    tools: list[ToolCallRecord] = []
    tool_status: dict[str, str] = {}
    products: list[dict[str, str | int]] | None = None
    payment_link: str | None = None
    reasoning_parts: list[str] = []

    for message in new_messages:
        if isinstance(message, AIMessage):
            if message.tool_calls and message.content:
                content = message.content
                if isinstance(content, str) and content.strip():
                    reasoning_parts.append(content.strip())
                elif isinstance(content, list):
                    parts = [
                        str(block.get("text", "")) for block in content if isinstance(block, dict)
                    ]
                    joined = "\n".join(part for part in parts if part).strip()
                    if joined:
                        reasoning_parts.append(joined)
            for tool_call in message.tool_calls or []:
                name = _tool_call_name(tool_call)
                tool_status[name] = "done"
                tools.append(
                    ToolCallRecord(
                        name=name,
                        status="done",
                        title=get_tool_title(name),
                    ),
                )
        elif isinstance(message, ToolMessage):
            name = message.name or "unknown"
            parsed = _safe_json_loads(message.content)
            if name == "list_b2c_products" and isinstance(parsed, dict):
                items = parsed.get("items")
                if isinstance(items, list):
                    catalog = [item for item in items if isinstance(item, dict)]
                    if catalog:
                        products = catalog
            if name == "create_payment_link" and isinstance(parsed, dict):
                url = parsed.get("url")
                if isinstance(url, str):
                    payment_link = url
            if getattr(message, "status", None) == "error":
                tool_status[name] = "error"
                for record in tools:
                    if record.name == name:
                        record.status = "error"

    final_message = _extract_final_text(new_messages)
    reasoning = _build_reasoning(reasoning_parts, tools)

    if products:
        products = filter_recommended_products(products, final_message)

    return TurnResult(
        new_messages=new_messages,
        final_message=final_message,
        reasoning=reasoning,
        tools=tools,
        products=products,
        payment_link=payment_link,
    )


def _extract_final_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content and not message.tool_calls:
            content = message.content
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                parts = [str(block.get("text", "")) for block in content if isinstance(block, dict)]
                return "\n".join(part for part in parts if part).strip()
    return ""


_MAX_INTERMEDIATE_SNIPPET = 200


def _build_reasoning(reasoning_parts: list[str], tools: list[ToolCallRecord]) -> str:
    """Operational trace for UI — never the final user-facing answer."""
    lines: list[str] = ["Анализ запроса пользователя."]

    lines.extend(
        part.strip()
        for part in reasoning_parts
        if part.strip() and len(part.strip()) <= _MAX_INTERMEDIATE_SNIPPET
    )

    if tools:
        lines.extend(f"Вызов инструмента: {tool.title}" for tool in tools)
        lines.append("Формирование рекомендации.")
    else:
        lines.append("Подготовка ответа без инструментов.")

    return "\n".join(lines)


def _tool_call_name(tool_call: object) -> str:
    if isinstance(tool_call, dict):
        name = tool_call.get("name")
        return name if isinstance(name, str) else "unknown"
    name = getattr(tool_call, "name", None)
    return name if isinstance(name, str) else "unknown"


def _safe_json_loads(content: str | list[str | dict[str, object]]) -> object:
    if isinstance(content, list):
        texts = [str(block.get("text", "")) for block in content if isinstance(block, dict)]
        content = "\n".join(text for text in texts if text)
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return content
