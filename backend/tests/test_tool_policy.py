"""Policy tests for confirm_payment / save_lead (FIX-3)."""

import json
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from mcp.types import Tool
from mcp_server.config import get_settings as get_mcp_settings
from mcp_server.data_access import catalog as catalog_module
from mcp_server.paths import leads_path
from mcp_server.tools.payment import handle_confirm_payment, handle_create_payment_link
from mcp_server.tools.save_lead import handle_save_lead

from app.core.config import get_settings
from app.mcp_client.context import TurnContext, clear_turn_context, set_turn_context
from app.mcp_client.runtime import apply_mcp_server_env
from app.mcp_client.tool_adapter import build_langchain_tools
from app.security.constants import LEAD_NAME_MAX_LENGTH
from app.security.tool_policy import apply_tool_policy


@pytest.fixture
def policy_data_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Path, None, None]:
    repo_data = Path(__file__).resolve().parents[2] / "data"
    target = tmp_path / "data"
    shutil.copytree(repo_data, target)
    (target / "leads.txt").write_text("# leads\n", encoding="utf-8")
    payments = target / "payments.json"
    if payments.exists():
        payments.unlink()
    monkeypatch.setenv("DATA_DIR", str(target))
    monkeypatch.setenv("SECURITY_ENABLED", "true")
    get_settings.cache_clear()
    get_mcp_settings.cache_clear()
    catalog_module.clear_cache()
    apply_mcp_server_env(get_settings())
    yield target
    get_settings.cache_clear()
    get_mcp_settings.cache_clear()
    catalog_module.clear_cache()
    clear_turn_context()


def _context(session_id: str = "sess-policy") -> TurnContext:
    return TurnContext(session_id=session_id, channel="web")


def test_save_lead_catalog_product_requires_confirm(policy_data_dir: Path) -> None:
    del policy_data_dir
    ctx = _context()
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "Иван",
            "phone": "+79990001122",
            "email": "ivan@example.com",
            "product_id": "agents",
            "segment": "b2c",
        },
        ctx,
        security_enabled=True,
    )
    assert err is not None
    assert "confirmed" in err


def test_save_lead_b2b_segment_does_not_bypass_catalog_confirm(policy_data_dir: Path) -> None:
    del policy_data_dir
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "Иван",
            "phone": "+79990001122",
            "email": "ivan@example.com",
            "product_id": "agents",
            "segment": "b2b",
        },
        _context(),
        security_enabled=True,
    )
    assert err is not None


def test_b2c_funnel_allows_save_lead_after_confirm(policy_data_dir: Path) -> None:
    del policy_data_dir
    session_id = "sess-funnel-ok"
    handle_create_payment_link("agents", session_id)
    handle_confirm_payment(session_id, "agents")
    ctx = _context(session_id)
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "Покупатель",
            "phone": "+79990000001",
            "email": "buyer@example.com",
            "product_id": "agents",
            "segment": "b2c",
        },
        ctx,
        security_enabled=True,
    )
    assert err is None
    result = handle_save_lead(
        "buyer@example.com",
        "+79990000001",
        "Покупатель",
        "agents",
        "web",
        "b2c",
    )
    assert result["ok"] is True
    lines = [line for line in leads_path().read_text(encoding="utf-8").splitlines() if "{" in line]
    assert len(lines) == 1


def test_b2b_non_catalog_save_lead_allowed(policy_data_dir: Path) -> None:
    del policy_data_dir
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "Корпклиент",
            "phone": "+79990000002",
            "email": "corp@example.com",
            "product_id": "custom-corp-workshop",
            "segment": "b2b",
        },
        _context(),
        security_enabled=True,
    )
    assert err is None


def test_save_lead_blocked_after_failed_confirm_same_turn(policy_data_dir: Path) -> None:
    del policy_data_dir
    ctx = _context()
    ctx.policy_state.confirm_payment_failed = True
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "Иван",
            "phone": "+79990001122",
            "email": "ivan@example.com",
            "product_id": "custom-corp-workshop",
            "segment": "b2b",
        },
        ctx,
        security_enabled=True,
    )
    assert err is not None
    assert "failed confirm_payment" in err


def test_confirm_unknown_product_blocked(policy_data_dir: Path) -> None:
    del policy_data_dir
    ctx = _context()
    err = apply_tool_policy(
        "confirm_payment",
        {"product_id": "not-a-course"},
        ctx,
        security_enabled=True,
    )
    assert err is not None
    assert ctx.policy_state.confirm_payment_failed is True


def test_lead_name_length_limit(policy_data_dir: Path) -> None:
    del policy_data_dir
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "x" * (LEAD_NAME_MAX_LENGTH + 1),
            "phone": "+7999",
            "email": "a@b.co",
            "product_id": "custom-corp-workshop",
            "segment": "b2b",
        },
        _context(),
        security_enabled=True,
    )
    assert err is not None
    assert "name exceeds" in err


def test_policy_inactive_when_security_disabled(policy_data_dir: Path) -> None:
    del policy_data_dir
    err = apply_tool_policy(
        "save_lead",
        {
            "name": "Иван",
            "phone": "+79990001122",
            "email": "ivan@example.com",
            "product_id": "agents",
            "segment": "b2c",
        },
        _context(),
        security_enabled=False,
    )
    assert err is None


def test_adapter_blocks_save_lead_without_confirm(policy_data_dir: Path) -> None:
    del policy_data_dir
    tools = build_langchain_tools(
        [
            Tool(
                name="save_lead",
                description="lead",
                inputSchema={"type": "object"},
            ),
        ],
    )
    set_turn_context(_context("sess-adapter"))
    payload = tools[0].invoke(
        {
            "email": "ivan@example.com",
            "phone": "+79990001122",
            "name": "Иван",
            "product_id": "agents",
            "segment": "b2c",
        },
    )
    assert isinstance(payload, str)
    body = json.loads(payload)
    assert "error" in body
    lines = [line for line in leads_path().read_text(encoding="utf-8").splitlines() if "{" in line]
    assert lines == []


def test_confirm_without_pending_marks_turn_and_blocks_save(policy_data_dir: Path) -> None:
    del policy_data_dir
    confirm_tools = build_langchain_tools(
        [
            Tool(
                name="confirm_payment",
                description="confirm",
                inputSchema={"type": "object"},
            ),
            Tool(
                name="save_lead",
                description="lead",
                inputSchema={"type": "object"},
            ),
        ],
    )
    ctx = _context("sess-no-pending")
    set_turn_context(ctx)
    confirm_payload = confirm_tools[0].invoke({"product_id": "agents"})
    assert isinstance(confirm_payload, str)
    confirm_body = json.loads(confirm_payload)
    assert "error" in confirm_body
    save_payload = confirm_tools[1].invoke(
        {
            "email": "ivan@example.com",
            "phone": "+79990001122",
            "name": "Иван",
            "product_id": "agents",
            "segment": "b2c",
        },
    )
    assert isinstance(save_payload, str)
    save_body = json.loads(save_payload)
    assert "error" in save_body
    lines = [line for line in leads_path().read_text(encoding="utf-8").splitlines() if "{" in line]
    assert lines == []
