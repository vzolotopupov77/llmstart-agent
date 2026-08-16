"""Tests for system prompt registry."""

import pytest

from app.agent.prompts import (
    SYSTEM_PROMPT_V1,
    SYSTEM_PROMPT_V2,
    SYSTEM_PROMPT_V3,
    SYSTEM_PROMPT_V4,
    SYSTEM_PROMPT_V6,
    get_default_system_prompt,
    get_system_prompt,
)


def test_get_system_prompt_v1() -> None:
    assert get_system_prompt("agent-system-prompt-v1") == SYSTEM_PROMPT_V1


def test_get_system_prompt_v2_differs_from_v1() -> None:
    v2 = get_system_prompt("agent-system-prompt-v2")
    assert v2 != SYSTEM_PROMPT_V1
    assert "search_knowledge_base" in v2
    assert v2.startswith(SYSTEM_PROMPT_V1)


def test_get_system_prompt_v3_differs_from_v2() -> None:
    v3 = get_system_prompt("agent-system-prompt-v3")
    assert v3 != SYSTEM_PROMPT_V2
    assert v3.startswith(SYSTEM_PROMPT_V2)
    assert "vibe-coding-intensive" in v3
    assert "Multi-turn" in v3


def test_get_system_prompt_v4_routing_rules() -> None:
    v4 = get_system_prompt("agent-system-prompt-v4")
    assert v4 != SYSTEM_PROMPT_V3
    assert v4.startswith(SYSTEM_PROMPT_V3)
    assert "vector_search" in v4
    assert "graph_search" in v4
    assert "global_catalog" in v4
    assert "text2cypher_tool" in v4
    assert "list_b2c_products" in v4
    assert "расписание" in v4
    assert "продолжения диалога о конкретном курсе" in v4


def test_get_system_prompt_v5_generation_fixes() -> None:
    v5 = get_system_prompt("agent-system-prompt-v5")
    assert v5 != SYSTEM_PROMPT_V4
    assert v5.startswith(SYSTEM_PROMPT_V4)
    assert "ai-agents-combo" in v5
    assert "consultation" in v5
    assert "рассрочк" in v5
    assert "vibe-coding-intensive" in v5
    assert "до ~2 часов" in v5


def test_get_system_prompt_unknown_raises() -> None:
    with pytest.raises(KeyError, match="Unknown prompt"):
        get_system_prompt("missing-prompt")


def test_get_system_prompt_v6_hardens_v1() -> None:
    v6 = get_system_prompt("agent-system-prompt-v6")
    assert v6 == SYSTEM_PROMPT_V6
    assert v6.startswith(SYSTEM_PROMPT_V1)
    assert "HACKED:" in v6
    assert "не обещай отправку email" in v6.lower() or "email" in v6.lower()
    assert "write-tools" in v6.lower() or "Write-tools" in v6


def test_get_default_system_prompt_follows_flag() -> None:
    assert get_default_system_prompt(security_enabled=True) == SYSTEM_PROMPT_V6
    assert get_default_system_prompt(security_enabled=False) == SYSTEM_PROMPT_V1
