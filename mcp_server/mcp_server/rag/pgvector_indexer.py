"""Knowledge base indexer into PostgreSQL pgvector."""

from __future__ import annotations

import logging

import psycopg
from pgvector.psycopg import register_vector

from mcp_server.config import Settings, get_settings
from mcp_server.paths import data_dir
from mcp_server.rag.embeddings import EmbeddingClient, MockEmbeddings, get_embedding_client
from mcp_server.rag.qdrant_indexer import (
    EMBED_BATCH_SIZE,
    UPSERT_BATCH_SIZE,
    IndexedChunk,
    _collect_indexed_chunks,
    _embed_in_batches,
    _scan_files,
    _stable_id,
)

logger = logging.getLogger(__name__)


def _ensure_extension(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()


def _ensure_schema(conn: psycopg.Connection, settings: Settings) -> None:
    dim = settings.embedding_dim
    table = settings.pgvector_table
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                source TEXT NOT NULL,
                segment TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding vector({dim}) NOT NULL
            )
            """,
        )
        cur.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_segment
            ON {table} (segment)
            """,
        )
        cur.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_embedding
            ON {table} USING hnsw (embedding vector_cosine_ops)
            """,
        )
    conn.commit()


def _upsert_in_batches(
    conn: psycopg.Connection,
    table: str,
    indexed_chunks: list[IndexedChunk],
    embeddings: list[list[float]],
    *,
    batch_size: int,
) -> None:
    with conn.cursor() as cur:
        for start in range(0, len(indexed_chunks), batch_size):
            batch_chunks = indexed_chunks[start : start + batch_size]
            batch_embeddings = embeddings[start : start + batch_size]
            for item, vector in zip(batch_chunks, batch_embeddings, strict=True):
                chunk_id = _stable_id(item.relative_path, item.chunk_index)
                cur.execute(
                    f"""
                    INSERT INTO {table} (
                        id, text, source, segment, relative_path, chunk_index, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        source = EXCLUDED.source,
                        segment = EXCLUDED.segment,
                        relative_path = EXCLUDED.relative_path,
                        chunk_index = EXCLUDED.chunk_index,
                        embedding = EXCLUDED.embedding
                    """,
                    (
                        chunk_id,
                        item.chunk.text,
                        item.chunk.source,
                        item.chunk.segment,
                        item.relative_path,
                        item.chunk_index,
                        vector,
                    ),
                )
    conn.commit()


def index(*, embedding_client: EmbeddingClient | None = None) -> int:
    """Index knowledge files into pgvector. Returns total chunk count."""
    settings = get_settings()
    root = data_dir()
    files = _scan_files(root)
    indexed_chunks = _collect_indexed_chunks(
        files,
        root=root,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    conn = psycopg.connect(settings.pgvector_conninfo)
    _ensure_extension(conn)
    register_vector(conn)
    _ensure_schema(conn, settings)

    if not indexed_chunks:
        logger.info("Done: %d files, 0 chunks indexed", len(files))
        conn.close()
        return 0

    embedder = embedding_client or get_embedding_client()
    if embedding_client is None and isinstance(embedder, MockEmbeddings):
        msg = "OPENAI_API_KEY is required for indexing"
        raise ValueError(msg)
    texts = [item.chunk.text for item in indexed_chunks]
    embeddings = _embed_in_batches(texts, embedder, batch_size=EMBED_BATCH_SIZE)
    _upsert_in_batches(
        conn,
        settings.pgvector_table,
        indexed_chunks,
        embeddings,
        batch_size=UPSERT_BATCH_SIZE,
    )
    conn.close()

    logger.info("Done: %d files, %d chunks indexed", len(files), len(indexed_chunks))
    return len(indexed_chunks)


def main() -> None:
    """CLI entrypoint for `make index BACKEND=pgvector`."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    index()


if __name__ == "__main__":
    main()
