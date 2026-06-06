"""Knowledge base retrieval from Chroma."""

from typing import Literal, TypedDict

import chromadb

from mcp_server.config import get_settings
from mcp_server.paths import chroma_dir
from mcp_server.rag.embeddings import EmbeddingClient, get_embedding_client
from mcp_server.rag.indexer import COLLECTION_NAME

Segment = Literal["b2b", "b2c"]


class KnowledgeChunk(TypedDict):
    """Single retrieved chunk."""

    text: str
    source: str
    segment: str


class IndexNotReadyError(Exception):
    """Raised when Chroma index is missing or empty."""


_INDEX_EMPTY_MSG = "knowledge base index is empty; run reindex first"


def _get_collection() -> chromadb.Collection:
    chroma_dir().mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir()))
    existing = {item.name for item in client.list_collections()}
    if COLLECTION_NAME not in existing:
        raise IndexNotReadyError(_INDEX_EMPTY_MSG)
    collection = client.get_collection(COLLECTION_NAME)
    if collection.count() == 0:
        raise IndexNotReadyError(_INDEX_EMPTY_MSG)
    return collection


def search_knowledge_base(
    query: str,
    segment: Segment,
    *,
    top_k: int | None = None,
    embedding_client: EmbeddingClient | None = None,
) -> list[KnowledgeChunk]:
    """Retrieve top-k chunks filtered by segment."""
    if segment not in ("b2b", "b2c"):
        msg = f"invalid segment: {segment}"
        raise ValueError(msg)

    collection = _get_collection()
    client = embedding_client or get_embedding_client()
    query_embedding = client.embed_texts([query])[0]
    limit = top_k if top_k is not None else get_settings().rag_top_k

    result = collection.query(
        query_embeddings=[query_embedding],  # type: ignore[arg-type]
        n_results=limit,
        where={"segment": segment},
    )

    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    chunks: list[KnowledgeChunk] = []
    for text, metadata in zip(documents[0], metadatas[0], strict=False):
        if not text or not metadata:
            continue
        chunks.append(
            {
                "text": text,
                "source": str(metadata.get("source", "")),
                "segment": str(metadata.get("segment", segment)),
            },
        )
    return chunks
