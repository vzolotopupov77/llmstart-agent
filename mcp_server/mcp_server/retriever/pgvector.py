"""Pgvector retriever implementation."""

from __future__ import annotations

import psycopg
from pgvector.psycopg import register_vector

from mcp_server.config import get_settings
from mcp_server.rag.embeddings import EmbeddingClient, get_embedding_client
from mcp_server.retriever.base import IndexNotReadyError, KnowledgeChunk, Segment

_INDEX_EMPTY_MSG = "knowledge base index is empty; run make index BACKEND=pgvector first"
_CONNECT_TIMEOUT = 10


class PgvectorRetriever:
    """Retrieve knowledge chunks from PostgreSQL pgvector table."""

    def __init__(
        self,
        *,
        embedding_client: EmbeddingClient | None = None,
        conninfo: str | None = None,
    ) -> None:
        settings = get_settings()
        self._table = settings.pgvector_table
        self._embedding_client = embedding_client or get_embedding_client()
        self._conninfo = conninfo or settings.pgvector_conninfo
        self._conn: psycopg.Connection | None = None
        self._ready = False

    def _get_conn(self) -> psycopg.Connection:
        """Return a cached connection, reopening if closed."""
        if self._conn is None or self._conn.closed:
            conn = psycopg.connect(self._conninfo, connect_timeout=_CONNECT_TIMEOUT)
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
            register_vector(conn)
            self._conn = conn
        return self._conn

    def close(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()
        self._conn = None

    def __del__(self) -> None:  # noqa: D105
        self.close()

    def _table_ready(self, conn: psycopg.Connection) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
                """,
                (self._table,),
            )
            row = cur.fetchone()
            if not row or not row[0]:
                return False
            cur.execute(f"SELECT COUNT(*) FROM {self._table}")
            count_row = cur.fetchone()
            return bool(count_row and count_row[0] > 0)

    def _ensure_ready(self) -> None:
        """Verify table exists and is non-empty once per retriever instance."""
        if self._ready:
            return
        conn = self._get_conn()
        if not self._table_ready(conn):
            raise IndexNotReadyError(_INDEX_EMPTY_MSG)
        self._ready = True

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        """Return top-k chunks from pgvector filtered by segment."""
        if segment not in ("b2b", "b2c"):
            msg = f"invalid segment: {segment}"
            raise ValueError(msg)

        self._ensure_ready()
        query_embedding = self._embedding_client.embed_texts([query])[0]
        conn = self._get_conn()

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT text, source, segment
                FROM {self._table}
                WHERE segment = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (segment, query_embedding, top_k),
            )
            rows = cur.fetchall()

        chunks: list[KnowledgeChunk] = []
        for text, source, row_segment in rows:
            if not text:
                continue
            chunks.append(
                {
                    "text": str(text),
                    "source": str(source),
                    "segment": str(row_segment),
                },
            )
        return chunks
