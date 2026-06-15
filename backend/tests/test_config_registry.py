"""Tests for AgentConfigRegistry (E-6)."""

from pathlib import Path

import pytest
from langchain_core.tools import BaseTool

from app.agent.config_registry import AgentConfigRegistry
from app.agent.react_runner import ReactRunner
from app.core.config import Settings
from app.core.exceptions import ConfigNotFoundError


class _StubTool(BaseTool):
    name: str = "stub_tool"
    description: str = "stub"

    def _run(self, *args: object, **kwargs: object) -> str:
        return "ok"

    async def _arun(self, *args: object, **kwargs: object) -> str:
        return "ok"


@pytest.fixture
def configs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "configs"


@pytest.fixture
def registry(configs_dir: Path) -> AgentConfigRegistry:
    settings = Settings(
        OPENAI_API_KEY="test-key",
        OPENAI_MODEL="openai/gpt-4o-mini",
    )
    return AgentConfigRegistry(settings, [_StubTool()], configs_dir)


def test_registry_loads_configs(registry: AgentConfigRegistry) -> None:
    ids = registry.list_config_ids()
    assert "baseline-react-chroma" in ids
    assert "benchmark-gpt-4o" in ids
    assert "candidate-rag-first-prompt" in ids
    assert "candidate-generation-keypoints-v3" in ids
    assert "candidate-rag-first-prompt-e2e-qa-v002" in ids


def test_different_config_ids_use_different_models(registry: AgentConfigRegistry) -> None:
    baseline_runner, baseline_id, baseline_model = registry.resolve_runner(
        "baseline-react-chroma",
    )
    benchmark_runner, benchmark_id, benchmark_model = registry.resolve_runner(
        "benchmark-gpt-4o",
    )
    assert baseline_id == "baseline-react-chroma"
    assert benchmark_id == "benchmark-gpt-4o"
    assert baseline_model == "openai/gpt-4o-mini"
    assert benchmark_model == "openai/gpt-4o"
    assert isinstance(baseline_runner, ReactRunner)
    assert isinstance(benchmark_runner, ReactRunner)
    assert baseline_runner is not benchmark_runner
    assert baseline_runner.model_name != benchmark_runner.model_name


def test_no_config_id_uses_env_defaults(registry: AgentConfigRegistry) -> None:
    runner, config_id, model = registry.resolve_runner(None)
    assert config_id is None
    assert model == "openai/gpt-4o-mini"
    assert runner.model_name == "openai/gpt-4o-mini"


def test_unknown_config_id_raises(registry: AgentConfigRegistry) -> None:
    with pytest.raises(ConfigNotFoundError):
        registry.resolve_runner("does-not-exist")


def test_different_prompt_configs_use_different_system_prompt(
    registry: AgentConfigRegistry,
) -> None:
    baseline_runner = registry.get_runner("baseline-react-chroma")
    candidate_runner = registry.get_runner("candidate-rag-first-prompt")
    assert baseline_runner.model_name == candidate_runner.model_name
    assert baseline_runner.system_prompt != candidate_runner.system_prompt
    assert "обязательно" in candidate_runner.system_prompt.lower()


def test_candidate_v3_differs_only_by_prompt(registry: AgentConfigRegistry) -> None:
    iter1 = registry.get_runner("candidate-rag-first-prompt")
    iter2 = registry.get_runner("candidate-generation-keypoints-v3")
    assert iter1.model_name == iter2.model_name
    assert iter1.system_prompt != iter2.system_prompt
    assert "vibe-coding-intensive" in iter2.system_prompt
