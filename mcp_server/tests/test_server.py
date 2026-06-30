"""MCP server integration tests."""

import asyncio

import pytest

from mcp_server.server import mcp

EXPECTED_TOOLS = {
    "vector_search",
    "graph_search",
    "global_catalog",
    "text2cypher_tool",
    "list_b2c_products",
    "create_payment_link",
    "confirm_payment",
    "save_lead",
}


@pytest.mark.asyncio
async def test_server_lists_eight_tools() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert names == EXPECTED_TOOLS


def test_server_list_tools_sync() -> None:
    """Fallback runner for environments without pytest-asyncio loop setup."""
    tools = asyncio.run(mcp.list_tools())
    assert len(tools) == len(EXPECTED_TOOLS)
