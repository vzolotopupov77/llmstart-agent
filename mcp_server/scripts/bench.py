"""Retriever benchmark runner for vector DB backends."""

from __future__ import annotations

import argparse
import json
import logging
import os
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from mcp_server.config import get_settings
from mcp_server.paths import data_dir
from mcp_server.rag.chunking import TextChunk, _window_text, chunk_markdown
from mcp_server.rag.embeddings import EmbeddingClient, get_embedding_client
from mcp_server.rag.qdrant_indexer import _read_text, _scan_files
from mcp_server.retriever.base import KnowledgeChunk, Segment
from mcp_server.retriever.chroma import ChromaRetriever
from mcp_server.retriever.pgvector import PgvectorRetriever
from mcp_server.retriever.qdrant import QdrantRetriever

logger = logging.getLogger(__name__)

DEFAULT_SCORE_THRESHOLD: float | None = None
LATENCY_RUNS = 5


class _CachingEmbeddings:
    """Wraps any EmbeddingClient; caches results by text to avoid redundant API calls.

    Each unique query text is embedded exactly once per bench run regardless of
    how many latency repetitions are performed.
    """

    def __init__(self, inner: EmbeddingClient) -> None:
        self._inner = inner
        self._cache: dict[str, list[float]] = {}

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        missing_texts: list[str] = []
        missing_indices: list[int] = []

        for i, text in enumerate(texts):
            if text in self._cache:
                results[i] = self._cache[text]
            else:
                missing_texts.append(text)
                missing_indices.append(i)

        if missing_texts:
            fetched = self._inner.embed_texts(missing_texts)
            for idx, text, vec in zip(missing_indices, missing_texts, fetched, strict=True):
                self._cache[text] = vec
                results[idx] = vec

        return [r for r in results if r is not None]


def _make_retriever(
    backend: str, embedding_client: EmbeddingClient
) -> QdrantRetriever | ChromaRetriever | PgvectorRetriever:
    """Create retriever for backend, injecting a shared embedding client."""
    if backend == "qdrant":
        return QdrantRetriever(embedding_client=embedding_client)
    if backend == "chroma":
        return ChromaRetriever(embedding_client=embedding_client)
    if backend == "pgvector":
        return PgvectorRetriever(embedding_client=embedding_client)
    msg = f"unknown backend: {backend}"
    raise ValueError(msg)


@dataclass(frozen=True)
class BenchQuery:
    """Single retrieval benchmark query."""

    query: str
    segment: Segment
    expected_text: str
    expected_source: str


def _load_config(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"Invalid bench config: {path}"
        raise TypeError(msg)
    return raw


def _rss_mb() -> float:
    if sys.platform == "win32":
        return 0.0
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss: int = usage.ru_maxrss
    if rss > 1_000_000:
        return rss / (1024 * 1024)
    return rss / 1024


def _chunk_file(path: Path, segment: str, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    content = _read_text(path)
    if path.suffix.lower() == ".md":
        return chunk_markdown(
            content,
            source=path.name,
            segment=segment,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    windows = _window_text(content, chunk_size=chunk_size, overlap=chunk_overlap)
    return [TextChunk(text=w, source=path.name, segment=segment) for w in windows]


def _build_bench_queries(chunk_size: int, chunk_overlap: int) -> list[BenchQuery]:
    root = data_dir()
    files = _scan_files(root)
    queries: list[BenchQuery] = []
    for path, raw_segment in files:
        if raw_segment not in ("b2b", "b2c"):
            continue
        seg: Segment = "b2b" if raw_segment == "b2b" else "b2c"
        chunks = [
            chunk
            for chunk in _chunk_file(path, raw_segment, chunk_size, chunk_overlap)
            if chunk.text.strip()
        ]
        for chunk in chunks[:3]:
            snippet = chunk.text.strip()[:80]
            if len(snippet) < 20:
                continue
            queries.append(
                BenchQuery(
                    query=snippet,
                    segment=seg,
                    expected_text=chunk.text,
                    expected_source=chunk.source,
                ),
            )
    return queries


def _index_backend(backend: str, embedding_client: EmbeddingClient) -> int:
    if backend == "qdrant":
        from mcp_server.rag.qdrant_indexer import index as qdrant_index

        return qdrant_index(embedding_client=embedding_client)
    if backend == "chroma":
        from mcp_server.rag.indexer import reindex

        return reindex(embedding_client=embedding_client)
    if backend == "pgvector":
        from mcp_server.rag.pgvector_indexer import index as pgvector_index

        return pgvector_index(embedding_client=embedding_client)
    msg = f"unknown backend: {backend}"
    raise ValueError(msg)


def _chunk_matches(result: KnowledgeChunk, expected: BenchQuery) -> bool:
    if result["source"] != expected.expected_source:
        return False
    return result["text"].strip() == expected.expected_text.strip()


def _precision_at_k(results: list[KnowledgeChunk], expected: BenchQuery, k: int) -> float:
    top = results[:k]
    if not top:
        return 0.0
    hits = sum(1 for item in top if _chunk_matches(item, expected))
    return hits / k


def _recall_at_k(results: list[KnowledgeChunk], expected: BenchQuery, k: int) -> float:
    top = results[:k]
    hits = sum(1 for item in top if _chunk_matches(item, expected))
    return float(hits)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def run_bench(
    config_path: Path,
    out_dir: Path,
    backend: str | None = None,
    *,
    skip_index: bool = False,
) -> Path:
    """Run benchmark for backend and write JSON report."""
    config = _load_config(config_path)
    retrieval = config.get("retrieval", {})
    top_k = int(retrieval.get("top_k", get_settings().rag_top_k))
    chunk_size = int(retrieval.get("chunk_size", get_settings().chunk_size))
    chunk_overlap = get_settings().chunk_overlap
    resolved_backend = backend or os.environ.get(
        "RETRIEVER_BACKEND",
        get_settings().retriever_backend,
    )

    # One caching embedding client shared across indexing and search phases.
    # Each unique text is embedded exactly once per bench run:
    # - during indexing: chunk texts are cached after first embed
    # - during latency runs: query texts hit the cache (no extra API calls)
    # This avoids hundreds of redundant OpenRouter calls across 3 backends.
    caching_embeddings = _CachingEmbeddings(get_embedding_client())

    if skip_index:
        logger.info("Skipping index (--skip-index); using existing vector store")
        indexed = 0
        index_time_s = 0.0
        index_rss_mb = _rss_mb()
    else:
        start_index = time.perf_counter()
        indexed = _index_backend(resolved_backend, caching_embeddings)
        index_time_s = time.perf_counter() - start_index
        index_rss_mb = _rss_mb()

    retriever = _make_retriever(resolved_backend, caching_embeddings)

    queries = _build_bench_queries(chunk_size, chunk_overlap)
    if not queries:
        msg = "no bench queries built from knowledge corpus"
        raise RuntimeError(msg)

    logger.info("Pre-warming embedding cache for %d queries...", len(queries))
    unique_texts = list({q.query for q in queries})
    caching_embeddings.embed_texts(unique_texts)
    logger.info("Embedding cache ready (%d unique texts)", len(unique_texts))

    latencies_ms: list[float] = []
    precisions: list[float] = []
    recalls: list[float] = []

    for query in queries:
        for _ in range(LATENCY_RUNS):
            start = time.perf_counter()
            retriever.search(query.query, query.segment, top_k=top_k)
            latencies_ms.append((time.perf_counter() - start) * 1000)

        results = retriever.search(query.query, query.segment, top_k=top_k)
        precisions.append(_precision_at_k(results, query, top_k))
        recalls.append(_recall_at_k(results, query, top_k))

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report = {
        "backend": resolved_backend,
        "timestamp": timestamp,
        "dataset": str(data_dir()),
        "top_k": top_k,
        "score_threshold": DEFAULT_SCORE_THRESHOLD,
        "indexed_chunks": indexed,
        "metrics": {
            "index_time_s": round(index_time_s, 3),
            "index_rss_mb": round(index_rss_mb, 2),
            "p50_latency_ms": round(_percentile(latencies_ms, 0.5), 2),
            "p95_latency_ms": round(_percentile(latencies_ms, 0.95), 2),
            "precision_at_k": round(statistics.mean(precisions), 4),
            "recall_at_k": round(statistics.mean(recalls), 4),
        },
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"vector-db-{resolved_backend}-{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Bench report written: %s", out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vector retriever benchmark")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--backend", default=None)
    parser.add_argument(
        "--skip-index",
        action="store_true",
        help="skip re-indexing; measure search latency only (requires make index)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_bench(args.config, args.out, backend=args.backend, skip_index=args.skip_index)


if __name__ == "__main__":
    main()
