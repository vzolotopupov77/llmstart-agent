"""Tests for eval run config loading."""

from pathlib import Path

from scripts.models import load_run_config

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def test_load_baseline_config() -> None:
    config = load_run_config(CONFIGS / "baseline-react-chroma.yaml")
    assert config.config_id == "baseline-react-chroma"
    assert config.model.name == "openai/gpt-4o-mini"
    assert config.retrieval.backend == "chroma-embedded"
    assert config.prompt.source == "code"
    assert config.datasets["e2e-qa"] == "v001"


def test_benchmark_differs_only_by_model() -> None:
    baseline = load_run_config(CONFIGS / "baseline-react-chroma.yaml")
    benchmark = load_run_config(CONFIGS / "benchmark-gpt-4o.yaml")
    assert benchmark.benchmark_only is True
    assert baseline.model.name != benchmark.model.name
    assert baseline.retrieval == benchmark.retrieval
    assert baseline.prompt == benchmark.prompt


def test_load_dataset_context_uses_config_pinned_version() -> None:
    from scripts.run_utils import load_dataset_context

    config = load_run_config(CONFIGS / "candidate-rag-first-prompt-e2e-qa-v002.yaml")
    ctx = load_dataset_context(config, "e2e-qa")
    assert ctx["dataset_version"] == "v002"
    assert ctx["langfuse_dataset"] == "e2e/e2e-qa/v002"
