"""Tests for Qdrant indexer file scanning."""

from pathlib import Path

from mcp_server.rag.qdrant_indexer import _scan_files


def _write(path: Path, content: str = "content") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_files_resolves_segment_at_any_depth(tmp_path: Path) -> None:
    _write(tmp_path / "b2b" / "corporate-training.md")
    _write(tmp_path / "b2c" / "faq-b2c.md")
    _write(tmp_path / "real_data" / "b2b" / "portfolio.pdf", "%PDF-1.4\n")
    _write(tmp_path / "real_data" / "b2c" / "programs" / "ai-agents-combo.md")

    scanned = dict(_scan_files(tmp_path))

    assert scanned[tmp_path / "b2b" / "corporate-training.md"] == "b2b"
    assert scanned[tmp_path / "b2c" / "faq-b2c.md"] == "b2c"
    assert scanned[tmp_path / "real_data" / "b2b" / "portfolio.pdf"] == "b2b"
    assert scanned[tmp_path / "real_data" / "b2c" / "programs" / "ai-agents-combo.md"] == "b2c"


def test_scan_files_skips_service_and_unsegmented_files(tmp_path: Path) -> None:
    _write(tmp_path / "b2b" / "corporate-training.md")
    _write(tmp_path / "leads.txt", '{"name": "test"}\n')
    _write(tmp_path / "payments.json", "{}\n")
    _write(tmp_path / "b2c" / "catalog.json", '{"items": []}\n')
    _write(tmp_path / "orphan.md", "no segment folder")

    scanned = _scan_files(tmp_path)

    assert len(scanned) == 1
    assert scanned[0][1] == "b2b"
