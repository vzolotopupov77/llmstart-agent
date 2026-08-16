"""Convert MCP tools to LangChain StructuredTools."""

import json
from typing import Any

from langchain_core.tools import StructuredTool
from mcp.types import Tool

from app.core.config import get_settings
from app.mcp_client.context import get_turn_context
from app.mcp_client.sync_tools import execute_tool
from app.mcp_client.tool_schemas import TOOL_ARGS_SCHEMAS
from app.security.tool_policy import apply_tool_policy, mark_confirm_payment_result

TOOL_TITLES: dict[str, str] = {
    "vector_search": "Семантический поиск",
    "graph_search": "Графовый поиск",
    "global_catalog": "Обзор каталога",
    "text2cypher_tool": "Структурный запрос к графу",
    "list_b2c_products": "Каталог курсов",
    "create_payment_link": "Создание ссылки на оплату",
    "confirm_payment": "Подтверждение оплаты",
    "save_lead": "Сохранение лида",
}

SESSION_INJECTED_TOOLS = frozenset({"create_payment_link", "confirm_payment"})
CHANNEL_INJECTED_TOOLS = frozenset({"save_lead"})


def build_langchain_tools(tools: list[Tool]) -> list[StructuredTool]:
    """Build LangChain tools from MCP tool definitions."""
    return [_build_tool(tool) for tool in tools]


def _build_tool(tool: Tool) -> StructuredTool:
    def _run_sync(**kwargs: Any) -> str:
        """Sync entrypoint for LangGraph tool node."""
        arguments = _inject_context(tool.name, kwargs)
        settings = get_settings()
        if tool.name in {"confirm_payment", "save_lead"}:
            context = get_turn_context()
            policy_error = apply_tool_policy(
                tool.name,
                arguments,
                context,
                security_enabled=settings.security_enabled,
            )
            if policy_error is not None:
                result = {"error": policy_error}
                if tool.name == "confirm_payment":
                    mark_confirm_payment_result(context, result)
                return json.dumps(result, ensure_ascii=False)
        result = execute_tool(tool.name, arguments)
        if tool.name == "confirm_payment":
            mark_confirm_payment_result(get_turn_context(), result)
        return json.dumps(result, ensure_ascii=False)

    args_schema = TOOL_ARGS_SCHEMAS.get(tool.name)
    return StructuredTool.from_function(
        func=_run_sync,
        name=tool.name,
        description=tool.description or tool.name,
        args_schema=args_schema,
    )


def _inject_context(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Inject session_id/channel from turn context where required."""
    payload = dict(arguments)
    if tool_name in SESSION_INJECTED_TOOLS or tool_name in CHANNEL_INJECTED_TOOLS:
        context = get_turn_context()
        if tool_name in SESSION_INJECTED_TOOLS:
            payload["session_id"] = context.session_id
        if tool_name in CHANNEL_INJECTED_TOOLS:
            payload["channel"] = context.channel
    return payload


def get_tool_title(name: str) -> str:
    """Human-readable tool title for API responses."""
    return TOOL_TITLES.get(name, name)
