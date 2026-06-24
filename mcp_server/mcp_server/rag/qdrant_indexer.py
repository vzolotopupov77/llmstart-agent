"""Knowledge base indexer into Qdrant."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, PointStruct, VectorParams

from mcp_server.config import Settings, get_settings
from mcp_server.paths import data_dir
from mcp_server.rag.chunking import TextChunk, chunk_markdown
from mcp_server.rag.embeddings import EmbeddingClient, MockEmbeddings, get_embedding_client

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}
KNOWN_SEGMENTS = frozenset({"b2b", "b2c"})
SERVICE_RELATIVE_PATHS = frozenset(
    {
        Path("leads.txt"),
        Path("payments.json"),
        Path("b2c") / "catalog.json",
    },
)
UPSERT_BATCH_SIZE = 64
EMBED_BATCH_SIZE = 64


@dataclass(frozen=True)
class IndexedChunk:
    """Chunk ready for Qdrant upsert."""

    chunk: TextChunk
    relative_path: str
    chunk_index: int


def _resolve_segment(relative: Path) -> str | None:
    """Return b2b/b2c from any directory level (e.g. real_data/b2c/programs/)."""
    for part in relative.parts:
        if part in KNOWN_SEGMENTS:
            return part
    return None


def _is_service_file(relative: Path) -> bool:
    """Skip runtime/state files that are not knowledge base content."""
    return relative in SERVICE_RELATIVE_PATHS


def _scan_files(root: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    if not root.exists():
        return files
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if _is_service_file(relative):
            continue
        segment = _resolve_segment(relative)
        if segment is None:
            continue
        files.append((path, segment))
    return files


def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8")


def _chunk_text(
    content: str,
    *,
    path: Path,
    segment: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    """Chunk text: markdown gets heading-split first; other formats window-only."""
    if path.suffix.lower() == ".md":
        return chunk_markdown(
            content,
            source=path.name,
            segment=segment,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    from mcp_server.rag.chunking import _window_text  # noqa: PLC0415

    windows = _window_text(content, chunk_size=chunk_size, overlap=chunk_overlap)
    return [TextChunk(text=w, source=path.name, segment=segment) for w in windows]


def _stable_id(relative_path: str, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{relative_path}:{chunk_index}"))


def _ensure_collection(client: QdrantClient, settings: Settings) -> None:
    collection_name = settings.qdrant_collection
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
        )
    client.create_payload_index(
        collection_name=collection_name,
        field_name="segment",
        field_schema=PayloadSchemaType.KEYWORD,
    )


def _collect_indexed_chunks(
    files: list[tuple[Path, str]],
    *,
    root: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> list[IndexedChunk]:
    indexed: list[IndexedChunk] = []
    for path, segment in files:
        relative_path = str(path.relative_to(root))
        content = _read_text(path)
        chunks = [
            c
            for c in _chunk_text(
                content,
                path=path,
                segment=segment,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            if c.text.strip()
        ]
        logger.info("Processing %s: %d chunks", relative_path, len(chunks))
        indexed.extend(
            IndexedChunk(
                chunk=chunk,
                relative_path=relative_path,
                chunk_index=index,
            )
            for index, chunk in enumerate(chunks)
        )
    return indexed


def _embed_in_batches(
    texts: list[str],
    embedding_client: EmbeddingClient,
    *,
    batch_size: int,
) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        embeddings.extend(embedding_client.embed_texts(batch))
    return embeddings


def _upsert_in_batches(
    client: QdrantClient,
    collection_name: str,
    indexed_chunks: list[IndexedChunk],
    embeddings: list[list[float]],
    *,
    batch_size: int,
) -> None:
    for start in range(0, len(indexed_chunks), batch_size):
        batch_chunks = indexed_chunks[start : start + batch_size]
        batch_embeddings = embeddings[start : start + batch_size]
        points = [
            PointStruct(
                id=_stable_id(item.relative_path, item.chunk_index),
                vector=vector,
                payload={
                    "text": item.chunk.text,
                    "source": item.chunk.source,
                    "segment": item.chunk.segment,
                    "relative_path": item.relative_path,
                    "chunk_index": item.chunk_index,
                },
            )
            for item, vector in zip(batch_chunks, batch_embeddings, strict=True)
        ]
        client.upsert(collection_name=collection_name, points=points)


def index(*, embedding_client: EmbeddingClient | None = None) -> int:
    """Index knowledge files into Qdrant. Returns total chunk count."""
    settings = get_settings()
    root = data_dir()
    files = _scan_files(root)
    indexed_chunks = _collect_indexed_chunks(
        files,
        root=root,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )
    _ensure_collection(client, settings)

    if not indexed_chunks:
        logger.info("Done: %d files, 0 chunks indexed", len(files))
        return 0

    embedder = embedding_client or get_embedding_client()
    if embedding_client is None and isinstance(embedder, MockEmbeddings):
        msg = "OPENAI_API_KEY is required for indexing"
        raise ValueError(msg)
    texts = [item.chunk.text for item in indexed_chunks]
    embeddings = _embed_in_batches(texts, embedder, batch_size=EMBED_BATCH_SIZE)
    _upsert_in_batches(
        client,
        settings.qdrant_collection,
        indexed_chunks,
        embeddings,
        batch_size=UPSERT_BATCH_SIZE,
    )

    logger.info("Done: %d files, %d chunks indexed", len(files), len(indexed_chunks))
    return len(indexed_chunks)


def main() -> None:
    """CLI entrypoint for `make index`."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    index()


if __name__ == "__main__":
    main()
