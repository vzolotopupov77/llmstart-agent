"""MCP stdio server with LLMStart tools."""

import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP

from mcp_server.retriever.base import KnowledgeChunk
from mcp_server.tools.list_b2c_products import handle_list_b2c_products
from mcp_server.tools.payment import handle_confirm_payment, handle_create_payment_link
from mcp_server.tools.save_lead import handle_save_lead
from mcp_server.tools.search_knowledge_base import (
    GLOBAL_CATALOG_TOOL_DESCRIPTION,
    GRAPH_SEARCH_TOOL_DESCRIPTION,
    VECTOR_SEARCH_TOOL_DESCRIPTION,
    handle_branch_search,
)
from mcp_server.tools.text2cypher import TEXT2CYPHER_TOOL_DESCRIPTION, handle_text2cypher

logger = logging.getLogger(__name__)

mcp = FastMCP("llmstart-tools", json_response=True)


@mcp.tool()
def vector_search(query: str, segment: Literal["b2b", "b2c"]) -> list[KnowledgeChunk]:
    """Semantic search for single-hop questions about courses, FAQ, and policies."""
    return handle_branch_search(query, segment, "vector")


@mcp.tool()
def graph_search(query: str, segment: Literal["b2b", "b2c"]) -> list[KnowledgeChunk]:
    """Graph traversal for multi-hop prerequisites, dependencies, and theme intersections."""
    return handle_branch_search(query, segment, "graph")


@mcp.tool()
def global_catalog(query: str, segment: Literal["b2b", "b2c"]) -> list[KnowledgeChunk]:
    """Catalog-wide structural aggregates: formats, audiences, hours, theme coverage."""
    return handle_branch_search(query, segment, "global")


vector_search.__doc__ = VECTOR_SEARCH_TOOL_DESCRIPTION
graph_search.__doc__ = GRAPH_SEARCH_TOOL_DESCRIPTION
global_catalog.__doc__ = GLOBAL_CATALOG_TOOL_DESCRIPTION


@mcp.tool()
def text2cypher_tool(query: str, segment: Literal["b2b", "b2c"]) -> list[KnowledgeChunk]:
    """Run read-only structural Neo4j queries (counts/lists), not semantic descriptions."""
    return handle_text2cypher(query, segment)


text2cypher_tool.__doc__ = TEXT2CYPHER_TOOL_DESCRIPTION


@mcp.tool()
def list_b2c_products() -> dict[str, list[dict[str, str | int]]]:
    """List all B2C products from catalog.json."""
    return handle_list_b2c_products()


@mcp.tool()
def create_payment_link(product_id: str, session_id: str) -> dict[str, str]:
    """Create a mock payment checkout URL for a product and session."""
    return handle_create_payment_link(product_id, session_id)


@mcp.tool()
def confirm_payment(session_id: str, product_id: str) -> dict[str, str]:
    """Confirm mock payment for session and product (idempotent)."""
    return handle_confirm_payment(session_id, product_id)


@mcp.tool()
def save_lead(
    email: str,
    phone: str,
    name: str,
    product_id: str,
    channel: Literal["web", "telegram"],
    segment: Literal["b2b", "b2c"],
) -> dict[str, bool]:
    """Save lead contact to data/leads.txt (JSON Lines)."""
    return handle_save_lead(email, phone, name, product_id, channel, segment)


def main() -> None:
    """Start stdio MCP server."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
