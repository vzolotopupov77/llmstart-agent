"""Unit tests for in-process MCP tool execution."""

import pytest

from app.core.exceptions import McpUnavailableError
from app.mcp_client.sync_tools import execute_tool


def test_create_payment_link_requires_product_id() -> None:
    result = execute_tool(
        "create_payment_link",
        {"session_id": "sess-1"},
    )

    assert result == {"error": "missing required argument: product_id"}


def test_unknown_tool_raises_mcp_unavailable() -> None:
    with pytest.raises(McpUnavailableError):
        execute_tool("unknown_tool", {})
