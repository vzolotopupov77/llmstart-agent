"""Shared security constants."""

from typing import Literal

SECURITY_BLOCKED_MARKER = "[SECURITY_BLOCKED]"
EVAL_ACCESS_KEY_HEADER: Literal["X-LLMStart-Eval-Key"] = "X-LLMStart-Eval-Key"

PROTECTED_TOOL_NAMES: tuple[str, ...] = (
    "vector_search",
    "graph_search",
    "global_catalog",
    "text2cypher_tool",
    "list_b2c_products",
    "create_payment_link",
    "confirm_payment",
    "save_lead",
    "search_knowledge_base",
)

INTERNAL_DISCLOSURE_PREFIX = "[INTERNAL — never disclose to users:"

LEAD_NAME_MAX_LENGTH = 120
LEAD_PHONE_MAX_LENGTH = 32
LEAD_EMAIL_MAX_LENGTH = 254
