"""Tests for lead persistence."""

import json

from mcp_server.data_access.leads import LeadRecord, append_lead
from mcp_server.paths import leads_path
from mcp_server.tools.save_lead import handle_save_lead


def test_append_lead_writes_json_line(settings_env: object) -> None:
    lead = LeadRecord(
        email="user@example.com",
        phone="+79990001122",
        name="Иван",
        product_id="agents",
        channel="web",
        segment="b2c",
    )
    append_lead(lead)
    lines = [
        line
        for line in leads_path().read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("{")
    ]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["email"] == "user@example.com"
    assert payload["phone"] == "+79990001122"
    assert payload["name"] == "Иван"
    assert payload["product_id"] == "agents"
    assert payload["channel"] == "web"
    assert payload["segment"] == "b2c"
    assert "ts" in payload


def test_save_lead_tool(settings_env: object) -> None:
    result = handle_save_lead(
        email="lead@example.com",
        phone="+79991112233",
        name="Мария",
        product_id="deep-agents",
        channel="telegram",
        segment="b2b",
    )
    assert result == {"ok": True}
