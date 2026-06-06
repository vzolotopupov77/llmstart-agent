"""Static MCP tool definitions (mirrors mcp_server/server.py)."""

from mcp.types import Tool

from app.mcp_client.tool_schemas import (
    ConfirmPaymentArgs,
    CreatePaymentLinkArgs,
    ListB2cProductsArgs,
    SaveLeadArgs,
    SearchKnowledgeBaseArgs,
)


def get_tool_definitions() -> list[Tool]:
    """Return the five LLMStart tools for LangChain binding."""
    return [
        Tool(
            name="search_knowledge_base",
            description="Search B2B or B2C knowledge base and return relevant text chunks.",
            inputSchema=SearchKnowledgeBaseArgs.model_json_schema(),
        ),
        Tool(
            name="list_b2c_products",
            description="List all B2C products from catalog.json.",
            inputSchema=ListB2cProductsArgs.model_json_schema(),
        ),
        Tool(
            name="create_payment_link",
            description=(
                "Create a mock payment checkout URL. Requires product_id "
                "(catalog code, e.g. agents). session_id is injected by the system."
            ),
            inputSchema=CreatePaymentLinkArgs.model_json_schema(),
        ),
        Tool(
            name="confirm_payment",
            description=(
                "Confirm mock payment for a product. Requires product_id. "
                "session_id is injected by the system."
            ),
            inputSchema=ConfirmPaymentArgs.model_json_schema(),
        ),
        Tool(
            name="save_lead",
            description="Save lead contact to data/leads.txt (JSON Lines). channel is injected.",
            inputSchema=SaveLeadArgs.model_json_schema(),
        ),
    ]


EXPECTED_TOOL_COUNT = 5
