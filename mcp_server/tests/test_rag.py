"""Tests for RAG indexer and retriever."""

import os
import time
from pathlib import Path

import pytest

from mcp_server.rag.chunking import chunk_markdown
from mcp_server.rag.embeddings import MockEmbeddings
from mcp_server.rag.indexer import index_is_stale, reindex
from mcp_server.rag.retriever import search_knowledge_base
from mcp_server.tools.search_knowledge_base import handle_search_knowledge_base


def test_chunk_markdown_splits_by_heading() -> None:
    content = "# Title\n\n## Section A\n\nAlpha text.\n\n## Section B\n\nBeta text."
    chunks = chunk_markdown(
        content,
        source="demo.md",
        segment="b2c",
        chunk_size=200,
        chunk_overlap=20,
    )
    assert len(chunks) >= 2
    assert all(chunk.segment == "b2c" for chunk in chunks)


def test_reindex_and_search_b2c(
    settings_env: object,
    mock_embeddings: MockEmbeddings,
) -> None:
    count = reindex(embedding_client=mock_embeddings)
    assert count > 0
    results = search_knowledge_base(
        "ai-agents-combo отдельно",
        "b2c",
        embedding_client=mock_embeddings,
    )
    assert results
    assert all(item["segment"] == "b2c" for item in results)
    combined = " ".join(item["text"].lower() for item in results)
    assert "combo" in combined or "отдельности" in combined


def test_search_b2b_segment(
    indexed_data: Path,
    mock_embeddings: MockEmbeddings,
) -> None:
    results = search_knowledge_base(
        "корпоративное обучение команды",
        "b2b",
        embedding_client=mock_embeddings,
    )
    assert results
    assert all(item["segment"] == "b2b" for item in results)


def test_search_knowledge_base_tool(indexed_data: Path) -> None:
    chunks = handle_search_knowledge_base("Cursor интенсив", "b2c")
    assert chunks
    assert chunks[0]["segment"] == "b2c"


def test_reindex_after_source_change(
    settings_env: object,
    mock_embeddings: MockEmbeddings,
    tmp_data_dir: Path,
) -> None:
    reindex(embedding_client=mock_embeddings)
    assert index_is_stale() is False
    faq = tmp_data_dir / "b2c" / "faq-b2c.md"
    faq.write_text(
        faq.read_text(encoding="utf-8") + "\n\n## New\n\nFresh content.",
        encoding="utf-8",
    )
    time.sleep(0.05)
    os.utime(faq, (time.time() + 2, time.time() + 2))
    assert index_is_stale() is True
    new_count = reindex(embedding_client=mock_embeddings)
    assert new_count > 0
    assert index_is_stale() is False


def test_invalid_segment_raises(settings_env: object) -> None:
    with pytest.raises(ValueError, match="segment"):
        handle_search_knowledge_base("test", "invalid")  # type: ignore[arg-type]
