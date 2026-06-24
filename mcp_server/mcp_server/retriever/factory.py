"""Retriever factory driven by RETRIEVER_BACKEND."""

from functools import lru_cache

from mcp_server.config import get_settings
from mcp_server.retriever.base import BaseRetriever
from mcp_server.retriever.chroma import ChromaRetriever
from mcp_server.retriever.pgvector import PgvectorRetriever
from mcp_server.retriever.qdrant import QdrantRetriever


def _create_retriever(backend: str) -> BaseRetriever:
    match backend:
        case "qdrant":
            return QdrantRetriever()
        case "chroma":
            return ChromaRetriever()
        case "pgvector":
            return PgvectorRetriever()
        case _:
            msg = f"unknown RETRIEVER_BACKEND: {backend}"
            raise ValueError(msg)


@lru_cache
def _cached_retriever() -> BaseRetriever:
    return _create_retriever(get_settings().retriever_backend)


def get_retriever(*, backend: str | None = None) -> BaseRetriever:
    """Return retriever for configured or explicit backend."""
    if backend is not None:
        return _create_retriever(backend)
    return _cached_retriever()
