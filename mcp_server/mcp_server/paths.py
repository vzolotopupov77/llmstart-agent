"""Filesystem paths for MCP data access."""

from pathlib import Path

from mcp_server.config import get_settings


def data_dir() -> Path:
    """Root data directory."""
    return get_settings().data_dir.resolve()


def b2b_dir() -> Path:
    """B2B knowledge base directory."""
    return data_dir() / "b2b"


def b2c_dir() -> Path:
    """B2C knowledge base directory."""
    return data_dir() / "b2c"


def catalog_path() -> Path:
    """B2C product catalog JSON file."""
    return b2c_dir() / "catalog.json"


def leads_path() -> Path:
    """Leads append-only file."""
    return data_dir() / "leads.txt"


def payments_path() -> Path:
    """Mock payment state file."""
    return data_dir() / "payments.json"


def chroma_dir() -> Path:
    """Chroma persistence directory."""
    return data_dir() / ".chroma"


def index_manifest_path() -> Path:
    """Indexer manifest with source file mtimes."""
    return chroma_dir() / "manifest.json"
