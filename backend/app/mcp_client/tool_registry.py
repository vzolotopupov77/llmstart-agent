"""Static MCP tool definitions (mirrors mcp_server/server.py)."""

from mcp.types import Tool
from mcp_server.tools.search_knowledge_base import (
    GLOBAL_CATALOG_TOOL_DESCRIPTION,
    GRAPH_SEARCH_TOOL_DESCRIPTION,
    VECTOR_SEARCH_TOOL_DESCRIPTION,
)
from mcp_server.tools.text2cypher import TEXT2CYPHER_TOOL_DESCRIPTION

from app.mcp_client.tool_schemas import (
    BranchSearchArgs,
    ConfirmPaymentArgs,
    CreatePaymentLinkArgs,
    ListB2cProductsArgs,
    SaveLeadArgs,
)


def get_tool_definitions() -> list[Tool]:
    """Return LLMStart tools for LangChain binding."""
    branch_schema = BranchSearchArgs.model_json_schema()
    return [
        Tool(
            name="vector_search",
            description=VECTOR_SEARCH_TOOL_DESCRIPTION,
            inputSchema=branch_schema,
        ),
        Tool(
            name="graph_search",
            description=GRAPH_SEARCH_TOOL_DESCRIPTION,
            inputSchema=branch_schema,
        ),
        Tool(
            name="global_catalog",
            description=GLOBAL_CATALOG_TOOL_DESCRIPTION,
            inputSchema=branch_schema,
        ),
        Tool(
            name="text2cypher_tool",
            description=TEXT2CYPHER_TOOL_DESCRIPTION,
            inputSchema=branch_schema,
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


EXPECTED_TOOL_COUNT = 8
