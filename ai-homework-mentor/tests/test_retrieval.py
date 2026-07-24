"""Unit-тесты получения кода."""

from __future__ import annotations

from pathlib import Path

import pytest

from mentor.parser import Submission
from mentor.retrieval import CodeRetrievalError, build_code_index, retrieve_code


def test_retrieve_local_code_creates_index(tmp_path: Path) -> None:
    source = tmp_path / "student"
    source.mkdir()
    (source / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git" / "config").write_text("git", encoding="utf-8")

    workspace = tmp_path / "workspace"
    submission = Submission(source_type="local", source=str(source), topic="demo")

    code_dir = retrieve_code(submission, workspace)

    assert code_dir.exists()
    assert (code_dir / "main.py").exists()
    assert not (code_dir / ".git").exists()

    index_path = workspace / "code-index.md"
    assert index_path.exists()
    index_text = index_path.read_text(encoding="utf-8")
    assert "main.py" in index_text
    assert "**files:** 1" in index_text


def test_build_code_index_skips_binary(tmp_path: Path) -> None:
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "readme.txt").write_text("hello\n", encoding="utf-8")
    (code_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    workspace = tmp_path / "workspace"
    build_code_index(code_dir, workspace)

    index_text = (workspace / "code-index.md").read_text(encoding="utf-8")
    assert "readme.txt" in index_text
    assert "image.png" not in index_text


def test_retrieve_local_code_skips_env(tmp_path: Path) -> None:
    source = tmp_path / "student"
    source.mkdir()
    (source / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (source / ".env").write_text("SECRET=1\n", encoding="utf-8")

    workspace = tmp_path / "workspace"
    submission = Submission(source_type="local", source=str(source), topic="demo")

    retrieve_code(submission, workspace)

    assert (workspace / "code" / "main.py").exists()
    assert not (workspace / "code" / ".env").exists()


def test_retrieve_local_missing_dir_raises(tmp_path: Path) -> None:
    submission = Submission(
        source_type="local",
        source=str(tmp_path / "missing"),
        topic="demo",
    )
    with pytest.raises(CodeRetrievalError, match="не является директорией"):
        retrieve_code(submission, tmp_path / "workspace")


def test_retrieve_local_skips_dogfooding_dirs(tmp_path: Path) -> None:
    source = tmp_path / "student"
    source.mkdir()
    (source / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (source / "mentor").mkdir()
    (source / "mentor" / "cli.py").write_text("# cli\n", encoding="utf-8")
    (source / "tests").mkdir()
    (source / "tests" / "test_cli.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    for skip_name in ("workspace", "sprints", "concept"):
        skip_dir = source / skip_name
        skip_dir.mkdir()
        (skip_dir / "artifact.md").write_text("skip me\n", encoding="utf-8")

    workspace = tmp_path / "workspace"
    submission = Submission(source_type="local", source=str(source), topic="demo")

    retrieve_code(submission, workspace)

    code_dir = workspace / "code"
    assert (code_dir / "main.py").exists()
    assert (code_dir / "mentor" / "cli.py").exists()
    assert (code_dir / "tests" / "test_cli.py").exists()
    for skip_name in ("workspace", "sprints", "concept"):
        assert not (code_dir / skip_name).exists()

    index_text = (workspace / "code-index.md").read_text(encoding="utf-8")
    assert "artifact.md" not in index_text
    assert "mentor/cli.py" in index_text
