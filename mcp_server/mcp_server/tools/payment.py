"""Payment mock tool handlers."""

from mcp_server.data_access.payments import confirm_payment, create_payment_link


def handle_create_payment_link(product_id: str, session_id: str) -> dict[str, str]:
    """Generate mock checkout URL."""
    if not product_id.strip():
        msg = "product_id must not be empty"
        raise ValueError(msg)
    if not session_id.strip():
        msg = "session_id must not be empty"
        raise ValueError(msg)
    try:
        url = create_payment_link(product_id.strip(), session_id.strip())
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    return {"url": url}


def handle_confirm_payment(session_id: str, product_id: str) -> dict[str, str]:
    """Confirm mock payment (idempotent)."""
    if not product_id.strip():
        msg = "product_id must not be empty"
        raise ValueError(msg)
    if not session_id.strip():
        msg = "session_id must not be empty"
        raise ValueError(msg)
    try:
        status = confirm_payment(session_id.strip(), product_id.strip())
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    return {"status": status}
