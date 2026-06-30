"""Tests for eval run config loading."""

import yaml
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


def test_load_vector_db_baseline_config() -> None:
    config = load_run_config(CONFIGS / "vector-db-baseline.yaml")
    assert config.config_id == "vector-db-baseline"
    assert config.retrieval.backend == "qdrant"
    assert config.retrieval.db_version == "v1.18.2"
    assert config.retrieval.embedding_model == "openai/text-embedding-3-small"
    assert config.retrieval.chunk_size == 800
    assert config.retrieval.top_k == 4
    assert config.datasets["e2e-qa"] == "v002"


def test_load_vector_db_chroma_config() -> None:
    config = load_run_config(CONFIGS / "vector-db-chroma.yaml")
    assert config.config_id == "vector-db-chroma"
    assert config.retrieval.backend == "chroma"
    assert config.retrieval.top_k == 4


def test_load_vector_db_pgvector_config() -> None:
    config = load_run_config(CONFIGS / "vector-db-pgvector.yaml")
    assert config.config_id == "vector-db-pgvector"
    assert config.retrieval.backend == "pgvector"
    assert config.retrieval.top_k == 4


def test_load_vector_db_qdrant_config() -> None:
    config = load_run_config(CONFIGS / "vector-db-qdrant.yaml")
    assert config.config_id == "vector-db-qdrant"
    assert config.retrieval.backend == "qdrant"
    assert config.retrieval.top_k == 4


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


def test_load_graphrag_dataset_context_from_bare_slug() -> None:
    from scripts.run_utils import load_dataset_context

    config = load_run_config(CONFIGS / "graphrag-graph.yaml")
    ctx = load_dataset_context(config, "multi-hop")
    assert ctx["group"] == "graphrag"
    assert ctx["dataset_version"] == "v002"
    assert ctx["langfuse_dataset"] == "graphrag/multi-hop/v002"


def test_load_graphrag_routing_config() -> None:
    config = load_run_config(CONFIGS / "graphrag-routing.yaml")
    raw = yaml.safe_load((CONFIGS / "graphrag-routing.yaml").read_text(encoding="utf-8"))
    assert config.config_id == "graphrag-routing"
    assert config.prompt.name == "agent-system-prompt-v4"
    assert raw["retrieval"]["branch"] == "agent-routing"
    assert config.datasets["multi-hop"] == "v002"
    assert config.datasets["global"] == "v001"
    assert config.datasets["e2e-qa"] == "v002"
