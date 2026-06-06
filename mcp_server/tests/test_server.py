"""MCP server integration tests."""

import asyncio

import pytest

from mcp_server.server import mcp


@pytest.mark.asyncio
async def test_server_lists_five_tools() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    expected = {
        "search_knowledge_base",
        "list_b2c_products",
        "create_payment_link",
        "confirm_payment",
        "save_lead",
    }
    assert names == expected


def test_server_list_tools_sync() -> None:
    """Fallback runner for environments without pytest-asyncio loop setup."""
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == 5
