"""MCP stdio server with LLMStart tools."""

import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP

from mcp_server.rag.embeddings import get_embedding_client
from mcp_server.rag.indexer import ensure_index
from mcp_server.rag.retriever import KnowledgeChunk
from mcp_server.tools.list_b2c_products import handle_list_b2c_products
from mcp_server.tools.payment import handle_confirm_payment, handle_create_payment_link
from mcp_server.tools.save_lead import handle_save_lead
from mcp_server.tools.search_knowledge_base import handle_search_knowledge_base

logger = logging.getLogger(__name__)

mcp = FastMCP("llmstart-tools", json_response=True)


@mcp.tool()
def search_knowledge_base(query: str, segment: Literal["b2b", "b2c"]) -> list[KnowledgeChunk]:
    """Search B2B or B2C knowledge base and return relevant text chunks."""
    return handle_search_knowledge_base(query, segment)


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
    """Start stdio MCP server after ensuring RAG index."""
    logging.basicConfig(level=logging.INFO)
    try:
        ensure_index(embedding_client=get_embedding_client())
    except ValueError:
        logger.warning("Skipping auto-reindex: OPENAI_API_KEY not configured")
    mcp.run()


if __name__ == "__main__":
    main()
