"""Retriever factory driven by RETRIEVER_BACKEND and RETRIEVER_BRANCH."""

from functools import lru_cache

from mcp_server.config import get_settings
from mcp_server.retriever.base import BaseRetriever
from mcp_server.retriever.chroma import ChromaRetriever
from mcp_server.retriever.global_agg import GlobalRetriever
from mcp_server.retriever.graph import GraphRetriever
from mcp_server.retriever.hybrid import HybridRetriever
from mcp_server.retriever.pgvector import PgvectorRetriever
from mcp_server.retriever.qdrant import QdrantRetriever


def _vector_impl(backend: str) -> BaseRetriever:
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


def _create_retriever(backend: str, branch: str) -> BaseRetriever:
    vector = _vector_impl(backend)
    match branch:
        case "vector":
            return vector
        case "graph":
            return GraphRetriever(vector=vector)
        case "global":
            return GlobalRetriever()
        case "hybrid":
            return HybridRetriever(
                vector=vector,
                graph=GraphRetriever(vector=vector),
            )
        case _:
            msg = f"unknown RETRIEVER_BRANCH: {branch}"
            raise ValueError(msg)


@lru_cache
def _cached_retriever() -> BaseRetriever:
    settings = get_settings()
    return _create_retriever(settings.retriever_backend, settings.retriever_branch)


def get_retriever(*, backend: str | None = None, branch: str | None = None) -> BaseRetriever:
    """Return retriever for configured or explicit backend and branch."""
    if backend is not None or branch is not None:
        settings = get_settings()
        return _create_retriever(
            backend or settings.retriever_backend,
            branch or settings.retriever_branch,
        )
    return _cached_retriever()
