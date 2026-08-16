"""Tests for security canary in ReactRunner system prompt."""

from pathlib import Path

import pytest
from langchain_core.tools import BaseTool

from app.agent.config_registry import AgentConfigRegistry
from app.agent.prompts import SYSTEM_PROMPT_V1, SYSTEM_PROMPT_V6
from app.agent.react_runner import ReactRunner, build_system_prompt
from app.core.config import Settings

CANARY = "LLMSTART-CANARY-7f3a91c2e5b04d68"


class _StubTool(BaseTool):
    name: str = "stub_tool"
    description: str = "stub"

    def _run(self, *args: object, **kwargs: object) -> str:
        return "ok"

    async def _arun(self, *args: object, **kwargs: object) -> str:
        return "ok"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="openai/gpt-4o-mini",
        SECURITY_CANARY_TOKEN=CANARY,
    )


def test_build_system_prompt_appends_canary() -> None:
    wrapped = build_system_prompt("Base prompt.", CANARY)
    assert wrapped.startswith("Base prompt.")
    assert CANARY in wrapped
    assert "never disclose" in wrapped.lower()


def test_build_system_prompt_skips_empty_canary() -> None:
    assert build_system_prompt("Base prompt.", "") == "Base prompt."


def test_default_runner_includes_canary(settings: Settings) -> None:
    runner = ReactRunner(settings, [_StubTool()])
    assert CANARY in runner.system_prompt
    assert SYSTEM_PROMPT_V6 in runner.system_prompt


def test_default_runner_uses_v1_when_security_disabled() -> None:
    settings = Settings(
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="openai/gpt-4o-mini",
        SECURITY_CANARY_TOKEN=CANARY,
        SECURITY_ENABLED=False,
    )
    runner = ReactRunner(settings, [_StubTool()])
    assert SYSTEM_PROMPT_V1 in runner.system_prompt
    assert SYSTEM_PROMPT_V6 not in runner.system_prompt
    assert CANARY in runner.system_prompt


def test_config_id_runner_includes_canary(settings: Settings) -> None:
    configs_dir = Path(__file__).resolve().parents[2] / "evals" / "configs"
    registry = AgentConfigRegistry(settings, [_StubTool()], configs_dir)
    baseline = registry.get_runner("baseline-react-chroma")
    candidate = registry.get_runner("candidate-rag-first-prompt")
    assert CANARY in baseline.system_prompt
    assert CANARY in candidate.system_prompt
    assert baseline.system_prompt != candidate.system_prompt


def test_custom_system_prompt_still_gets_canary(settings: Settings) -> None:
    custom = "Custom eval prompt body."
    runner = ReactRunner(settings, [_StubTool()], system_prompt=custom)
    assert custom in runner.system_prompt
    assert CANARY in runner.system_prompt
