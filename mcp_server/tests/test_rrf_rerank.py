"""Tests for RRF fusion and reranker fallbacks."""

from typing import TYPE_CHECKING, cast

import pytest

from mcp_server.config import get_settings
from mcp_server.retriever.factory import _cached_retriever
from mcp_server.retriever.fusion import merge_rrf, rrf_score
from mcp_server.retriever.reranker import rerank_chunks

if TYPE_CHECKING:
    from mcp_server.retriever.base import KnowledgeChunk


def test_rrf_score_decreases_with_rank() -> None:
    assert rrf_score(1, k=60) > rrf_score(2, k=60)


def test_merge_rrf_combines_lists() -> None:
    vector = [
        cast("KnowledgeChunk", {"text": "a", "source": "q", "segment": "b2c", "entity_id": "x"})
    ]
    graph = [
        cast("KnowledgeChunk", {"text": "b", "source": "n", "segment": "b2c", "entity_id": "y"})
    ]
    merged = merge_rrf(vector, graph, k=60)
    assert len(merged) == 2
    assert merged[0].get("rank", 0) >= merged[1].get("rank", 0)


def test_merge_rrf_boosts_shared_entity() -> None:
    shared = [
        cast(
            "KnowledgeChunk",
            {"text": "shared", "source": "s", "segment": "b2c", "entity_id": "agents"},
        )
    ]
    merged = merge_rrf(shared, shared, k=60)
    assert len(merged) == 1
    assert merged[0]["rank"] > rrf_score(1, k=60)


def test_rerank_disabled_returns_top_k(
    settings_env: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RERANKER_ENABLED", "false")
    get_settings.cache_clear()
    _cached_retriever.cache_clear()

    chunks = [
        cast("KnowledgeChunk", {"text": f"chunk-{index}", "source": "s", "segment": "b2c"})
        for index in range(5)
    ]
    result = rerank_chunks("query", chunks, top_k=2)
    assert len(result) == 2

    get_settings.cache_clear()
    _cached_retriever.cache_clear()
