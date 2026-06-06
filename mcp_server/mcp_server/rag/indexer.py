"""Knowledge base indexer into Chroma."""

import json
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from mcp_server.config import get_settings
from mcp_server.paths import b2b_dir, b2c_dir, chroma_dir, index_manifest_path
from mcp_server.rag.chunking import TextChunk, chunk_markdown
from mcp_server.rag.embeddings import EmbeddingClient, get_embedding_client

COLLECTION_NAME = "knowledge_base"


def _scan_markdown_files() -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for segment, directory in (("b2b", b2b_dir()), ("b2c", b2c_dir())):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            files.append((path, segment))
    return files


def _source_mtime_map(files: list[tuple[Path, str]]) -> dict[str, float]:
    root = get_settings().data_dir.resolve()
    return {str(path.resolve().relative_to(root)): path.stat().st_mtime for path, _ in files}


def _load_manifest() -> dict[str, float]:
    manifest_path = index_manifest_path()
    if not manifest_path.exists():
        return {}
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {str(key): float(value) for key, value in raw.get("sources", {}).items()}


def _save_manifest(source_mtimes: dict[str, float]) -> None:
    manifest_path = index_manifest_path()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"sources": source_mtimes}
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def index_is_stale() -> bool:
    """Return True when source files changed or index is empty."""
    files = _scan_markdown_files()
    if not files:
        return False
    current = _source_mtime_map(files)
    stored = _load_manifest()
    if not stored:
        return True
    collection = _get_collection(create_if_missing=False)
    if collection is None or collection.count() == 0:
        return True
    return current != stored


def _get_collection(*, create_if_missing: bool = True) -> Collection | None:
    chroma_dir().mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir()))
    if not create_if_missing:
        existing = {item.name for item in client.list_collections()}
        if COLLECTION_NAME not in existing:
            return None
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _collect_chunks(files: list[tuple[Path, str]]) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for path, segment in files:
        content = path.read_text(encoding="utf-8")
        chunks.extend(
            chunk_markdown(
                content,
                source=path.name,
                segment=segment,
                chunk_size=get_settings().chunk_size,
                chunk_overlap=get_settings().chunk_overlap,
            ),
        )
    return chunks


def reindex(*, embedding_client: EmbeddingClient | None = None) -> int:
    """Rebuild Chroma index from markdown sources. Returns chunk count."""
    files = _scan_markdown_files()
    chunks = _collect_chunks(files)
    client = embedding_client or get_embedding_client()

    chroma_dir().mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(chroma_dir()))
    existing = {item.name for item in chroma_client.list_collections()}
    if COLLECTION_NAME in existing:
        chroma_client.delete_collection(COLLECTION_NAME)
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if not chunks:
        _save_manifest(_source_mtime_map(files))
        return 0

    texts = [chunk.text for chunk in chunks]
    embeddings = client.embed_texts(texts)
    ids = [f"chunk-{index}" for index in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,  # type: ignore[arg-type]
        metadatas=[{"source": chunk.source, "segment": chunk.segment} for chunk in chunks],
    )
    _save_manifest(_source_mtime_map(files))
    return len(chunks)


def ensure_index(*, embedding_client: EmbeddingClient | None = None) -> None:
    """Reindex when manifest is stale or collection is empty."""
    if index_is_stale():
        reindex(embedding_client=embedding_client)
