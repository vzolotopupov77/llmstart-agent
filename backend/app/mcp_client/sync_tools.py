"""Synchronous in-process execution of mcp_server tool handlers."""

import logging
from collections.abc import Callable
from typing import Any, Literal, cast

from mcp_server.tools.list_b2c_products import handle_list_b2c_products
from mcp_server.tools.payment import handle_confirm_payment, handle_create_payment_link
from mcp_server.tools.save_lead import handle_save_lead
from mcp_server.tools.search_knowledge_base import handle_search_knowledge_base

from app.core.exceptions import McpUnavailableError

logger = logging.getLogger(__name__)

Segment = Literal["b2b", "b2c"]
Channel = Literal["web", "telegram"]


def _run_search_knowledge_base(arguments: dict[str, Any]) -> Any:
    segment = cast("Segment", arguments["segment"])
    return handle_search_knowledge_base(str(arguments["query"]), segment)


def _run_create_payment_link(arguments: dict[str, Any]) -> Any:
    return handle_create_payment_link(
        str(arguments["product_id"]),
        str(arguments["session_id"]),
    )


def _run_confirm_payment(arguments: dict[str, Any]) -> Any:
    return handle_confirm_payment(
        str(arguments["session_id"]),
        str(arguments["product_id"]),
    )


def _run_save_lead(arguments: dict[str, Any]) -> Any:
    channel = cast("Channel", arguments["channel"])
    segment = cast("Segment", arguments["segment"])
    return handle_save_lead(
        str(arguments["email"]),
        str(arguments["phone"]),
        str(arguments["name"]),
        str(arguments["product_id"]),
        channel,
        segment,
    )


_TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "search_knowledge_base": _run_search_knowledge_base,
    "list_b2c_products": lambda _arguments: handle_list_b2c_products(),
    "create_payment_link": _run_create_payment_link,
    "confirm_payment": _run_confirm_payment,
    "save_lead": _run_save_lead,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Run tool handler in-process (safe from LangGraph worker threads)."""
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        msg = f"Unknown tool: {name}"
        raise McpUnavailableError(msg)

    try:
        return handler(arguments)
    except KeyError as exc:
        missing = exc.args[0] if exc.args else "argument"
        logger.warning("Tool %s missing argument: %s", name, missing)
        return {"error": f"missing required argument: {missing}"}
    except (TypeError, ValueError) as exc:
        logger.warning("Tool %s failed: %s", name, exc)
        return {"error": str(exc)}
