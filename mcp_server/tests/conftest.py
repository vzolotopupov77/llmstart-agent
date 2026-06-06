"""Shared pytest fixtures."""

import json
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from mcp_server.config import Settings, get_settings
from mcp_server.data_access import catalog as catalog_module
from mcp_server.rag.embeddings import MockEmbeddings


@pytest.fixture
def repo_data_dir() -> Path:
    """Path to committed seed data in repo."""
    return Path(__file__).resolve().parents[2] / "data"


@pytest.fixture
def tmp_data_dir(tmp_path: Path, repo_data_dir: Path) -> Path:
    """Isolated data directory copied from seed data."""
    target = tmp_path / "data"
    shutil.copytree(repo_data_dir, target)
    return target


@pytest.fixture
def settings_env(
    tmp_data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[Settings, None, None]:
    """Point MCP settings to tmp data dir and clear cache."""
    monkeypatch.setenv("DATA_DIR", str(tmp_data_dir))
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    leads_file = tmp_data_dir / "leads.txt"
    leads_file.write_text("# LLMStart leads (JSON Lines)\n", encoding="utf-8")
    payments_file = tmp_data_dir / "payments.json"
    if payments_file.exists():
        payments_file.unlink()
    get_settings.cache_clear()
    catalog_module.clear_cache()
    yield get_settings()
    get_settings.cache_clear()
    catalog_module.clear_cache()


@pytest.fixture
def mock_embeddings() -> MockEmbeddings:
    """Deterministic embedding client for tests."""
    return MockEmbeddings()


@pytest.fixture
def indexed_data(settings_env: Settings, mock_embeddings: MockEmbeddings) -> Path:
    """Tmp data dir with built Chroma index."""
    from mcp_server.rag.indexer import reindex

    reindex(embedding_client=mock_embeddings)
    return settings_env.data_dir


@pytest.fixture
def sample_catalog_items() -> list[dict[str, str | int]]:
    """Expected number of catalog products."""
    catalog_path = Path(__file__).resolve().parents[2] / "data" / "b2c" / "catalog.json"
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    items: list[dict[str, str | int]] = payload["items"]
    return items
