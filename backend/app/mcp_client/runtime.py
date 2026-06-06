"""Bootstrap mcp_server data layer for in-process tool execution."""

import logging
import os

from mcp_server.config import get_settings as get_mcp_settings
from mcp_server.rag.embeddings import get_embedding_client
from mcp_server.rag.indexer import ensure_index

from app.core.config import Settings

logger = logging.getLogger(__name__)


def apply_mcp_server_env(settings: Settings) -> None:
    """Sync backend settings into os.environ for mcp_server handlers."""
    os.environ["DATA_DIR"] = str(settings.data_dir)
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    os.environ["OPENAI_BASE_URL"] = settings.openai_base_url
    os.environ["EMBEDDING_MODEL"] = settings.embedding_model
    os.environ["RAG_TOP_K"] = str(settings.rag_top_k)
    get_mcp_settings.cache_clear()


def ensure_rag_index() -> int:
    """Ensure Chroma index exists; return chunk count or 0 on skip."""
    try:
        count = ensure_index(embedding_client=get_embedding_client())
        return int(count) if count is not None else 0
    except ValueError:
        logger.warning("Skipping RAG index: OPENAI_API_KEY not configured")
        return 0
