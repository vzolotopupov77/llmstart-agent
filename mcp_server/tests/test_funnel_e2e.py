"""End-to-end funnel: payment link -> confirm -> save lead."""

import json

from mcp_server.paths import leads_path
from mcp_server.tools.payment import handle_confirm_payment, handle_create_payment_link
from mcp_server.tools.save_lead import handle_save_lead


def test_funnel_payment_to_lead(settings_env: object) -> None:
    session_id = "e2e-session-001"
    product_id = "ai-agents-combo"

    link = handle_create_payment_link(product_id, session_id)
    assert "url" in link

    confirm = handle_confirm_payment(session_id, product_id)
    assert confirm["status"] == "confirmed"

    save = handle_save_lead(
        email="buyer@example.com",
        phone="+79990000001",
        name="Покупатель",
        product_id=product_id,
        channel="web",
        segment="b2c",
    )
    assert save["ok"] is True

    lines = [
        line
        for line in leads_path().read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("{")
    ]
    assert len(lines) == 1
    lead = json.loads(lines[0])
    assert lead["email"] == "buyer@example.com"
    assert lead["product_id"] == product_id
    assert lead["channel"] == "web"
    assert lead["segment"] == "b2c"
    assert len(lead) == 7
