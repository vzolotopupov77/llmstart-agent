"""Unit-тесты парсера входа."""

from __future__ import annotations

from pathlib import Path

import pytest

from mentor.parser import Submission, parse_input, parse_source, write_submission_md


def test_parse_github_url() -> None:
    submission = parse_input("https://github.com/user/repo", "FastAPI homework")
    assert submission == Submission(
        source_type="github",
        source="https://github.com/user/repo",
        topic="FastAPI homework",
    )


def test_parse_github_url_without_scheme() -> None:
    source_type, normalized = parse_source("github.com/user/repo.git")
    assert source_type == "github"
    assert normalized == "https://github.com/user/repo"


def test_parse_local_path(tmp_path: Path) -> None:
    project_dir = tmp_path / "student-project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("print('hi')\n", encoding="utf-8")

    submission = parse_input(str(project_dir), "CLI utility")
    assert submission.source_type == "local"
    assert submission.source == str(project_dir.resolve())
    assert submission.topic == "CLI utility"


def test_parse_invalid_input_raises() -> None:
    with pytest.raises(ValueError, match="Не удалось распознать вход"):
        parse_input("not-a-valid-source")


def test_write_submission_md(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    submission = Submission(
        source_type="local",
        source=str(tmp_path / "project"),
        topic="Test topic",
    )
    path = write_submission_md(workspace, submission)
    content = path.read_text(encoding="utf-8")
    assert "**source_type:** local" in content
    assert "Test topic" in content
