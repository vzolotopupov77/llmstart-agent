"""Tests for system prompt registry."""

import pytest

from app.agent.prompts import (
    SYSTEM_PROMPT_V1,
    SYSTEM_PROMPT_V2,
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


def test_get_system_prompt_unknown_raises() -> None:
    with pytest.raises(KeyError, match="Unknown prompt"):
        get_system_prompt("missing-prompt")
