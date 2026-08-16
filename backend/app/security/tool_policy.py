"""Tool-call policy before execute_tool (FIX-3)."""

from __future__ import annotations

from typing import Any

from mcp_server.data_access.catalog import load_catalog
from mcp_server.data_access.payments import has_confirmed_payment

from app.mcp_client.context import TurnContext
from app.security.constants import (
    LEAD_EMAIL_MAX_LENGTH,
    LEAD_NAME_MAX_LENGTH,
    LEAD_PHONE_MAX_LENGTH,
)


def apply_tool_policy(
    tool_name: str,
    arguments: dict[str, Any],
    context: TurnContext,
    *,
    security_enabled: bool,
) -> str | None:
    """Return an error string to send to the model, or None to proceed."""
    if not security_enabled:
        return None
    if tool_name == "confirm_payment":
        return _policy_confirm_payment(arguments, context)
    if tool_name == "save_lead":
        return _policy_save_lead(arguments, context)
    return None


def mark_confirm_payment_result(context: TurnContext, result: object) -> None:
    """Record a failed confirm in this turn (policy or handler error)."""
    if _is_tool_error(result):
        context.policy_state.confirm_payment_failed = True


def _policy_confirm_payment(arguments: dict[str, Any], context: TurnContext) -> str | None:
    product_id = str(arguments.get("product_id", "")).strip()
    if not _is_catalog_product(product_id):
        context.policy_state.confirm_payment_failed = True
        return f"unknown product_id: {product_id}"
    return None


def _policy_save_lead(arguments: dict[str, Any], context: TurnContext) -> str | None:
    if context.policy_state.confirm_payment_failed:
        return "save_lead is not allowed after a failed confirm_payment in this turn"
    name = str(arguments.get("name", ""))
    phone = str(arguments.get("phone", ""))
    email = str(arguments.get("email", ""))
    if len(name) > LEAD_NAME_MAX_LENGTH:
        return f"name exceeds max length {LEAD_NAME_MAX_LENGTH}"
    if len(phone) > LEAD_PHONE_MAX_LENGTH:
        return f"phone exceeds max length {LEAD_PHONE_MAX_LENGTH}"
    if len(email) > LEAD_EMAIL_MAX_LENGTH:
        return f"email exceeds max length {LEAD_EMAIL_MAX_LENGTH}"

    product_id = str(arguments.get("product_id", "")).strip()
    segment = str(arguments.get("segment", "")).strip()
    in_catalog = _is_catalog_product(product_id)
    if in_catalog:
        if not has_confirmed_payment(context.session_id, product_id):
            return (
                "save_lead for a catalog product requires a confirmed payment "
                f"for product_id={product_id} in this session"
            )
        return None
    if segment != "b2b":
        return "unknown product_id is allowed only for segment=b2b"
    return None


def _is_catalog_product(product_id: str) -> bool:
    if not product_id:
        return False
    return load_catalog().get_by_code(product_id) is not None


def _is_tool_error(result: object) -> bool:
    if not isinstance(result, dict):
        return False
    return "error" in result
