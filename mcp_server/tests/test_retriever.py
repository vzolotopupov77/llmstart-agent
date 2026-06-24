"""Tests for retriever factory and backends."""

from unittest.mock import MagicMock

import pytest

from mcp_server.rag.embeddings import MockEmbeddings
from mcp_server.retriever.base import IndexNotReadyError
from mcp_server.retriever.chroma import ChromaRetriever
from mcp_server.retriever.factory import get_retriever
from mcp_server.retriever.pgvector import PgvectorRetriever
from mcp_server.retriever.qdrant import QdrantRetriever


def test_get_retriever_qdrant(settings_env: object) -> None:
    retriever = get_retriever(backend="qdrant")
    assert isinstance(retriever, QdrantRetriever)


def test_get_retriever_chroma(settings_env: object) -> None:
    retriever = get_retriever(backend="chroma")
    assert isinstance(retriever, ChromaRetriever)


def test_get_retriever_pgvector(settings_env: object) -> None:
    retriever = get_retriever(backend="pgvector")
    assert isinstance(retriever, PgvectorRetriever)


def test_get_retriever_unknown_backend_raises(settings_env: object) -> None:
    with pytest.raises(ValueError, match="unknown RETRIEVER_BACKEND"):
        get_retriever(backend="unknown")


def _qdrant_point(*, text: str = "hello", source: str = "a.md", segment: str = "b2b") -> MagicMock:
    point = MagicMock()
    point.payload = {"text": text, "source": source, "segment": segment}
    return point


def test_qdrant_readiness_check_cached() -> None:
    client = MagicMock()
    client.collection_exists.return_value = True
    collection_info = MagicMock()
    collection_info.points_count = 5
    client.get_collection.return_value = collection_info
    response = MagicMock()
    response.points = [_qdrant_point()]
    client.query_points.return_value = response

    retriever = QdrantRetriever(embedding_client=MockEmbeddings(), client=client)
    retriever.search("query one", "b2b", top_k=1)
    retriever.search("query two", "b2b", top_k=1)

    assert client.collection_exists.call_count == 1
    assert client.get_collection.call_count == 1
    assert client.query_points.call_count == 2


def test_qdrant_raises_when_collection_missing() -> None:
    client = MagicMock()
    client.collection_exists.return_value = False

    retriever = QdrantRetriever(embedding_client=MockEmbeddings(), client=client)

    with pytest.raises(IndexNotReadyError, match="knowledge base index is empty"):
        retriever.search("query", "b2b", top_k=1)

    client.get_collection.assert_not_called()
    client.query_points.assert_not_called()


def test_pgvector_readiness_check_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    table_ready_calls = 0

    def counting_table_ready(self: PgvectorRetriever, conn: object) -> bool:
        nonlocal table_ready_calls
        table_ready_calls += 1
        return True

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [("chunk text", "src.md", "b2b")]
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    retriever = PgvectorRetriever(embedding_client=MockEmbeddings())
    monkeypatch.setattr(retriever, "_get_conn", lambda: mock_conn)
    monkeypatch.setattr(PgvectorRetriever, "_table_ready", counting_table_ready)

    retriever.search("query one", "b2b", top_k=1)
    retriever.search("query two", "b2b", top_k=1)

    assert table_ready_calls == 1


def test_pgvector_raises_when_table_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    def always_empty(_self: PgvectorRetriever, _conn: object) -> bool:
        return False

    monkeypatch.setattr(PgvectorRetriever, "_table_ready", always_empty)

    retriever = PgvectorRetriever(embedding_client=MockEmbeddings())
    mock_conn = MagicMock()

    def get_conn() -> MagicMock:
        return mock_conn

    monkeypatch.setattr(retriever, "_get_conn", get_conn)

    with pytest.raises(IndexNotReadyError, match="knowledge base index is empty"):
        retriever.search("query", "b2b", top_k=1)
