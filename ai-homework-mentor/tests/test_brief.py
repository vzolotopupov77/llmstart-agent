"""Unit-тесты формирования брифов."""

from __future__ import annotations

from pathlib import Path

import pytest

from mentor.brief import (
    BriefError,
    build_brief,
    estimate_tokens,
    load_rubric_aspects,
    parse_aspect_from_brief_path,
    resolve_aspect_id,
    select_files_for_aspect,
)


def test_estimate_tokens() -> None:
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("") == 0


def test_parse_aspect_from_brief_path() -> None:
    assert parse_aspect_from_brief_path("briefs/brief-structure.md") == "structure"


def test_parse_aspect_invalid() -> None:
    with pytest.raises(BriefError):
        parse_aspect_from_brief_path("notes/review-structure.md")


def test_build_brief_includes_skill_section(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "code-index.md").write_text(
        "# Code Index\n\n## Tree\n\n- `main.py` (20 lines)\n",
        encoding="utf-8",
    )
    rubric_path = (
        Path(__file__).resolve().parents[1]
        / "mentor"
        / "config"
        / "rubrics"
        / "fastapi-service.yaml"
    )
    aspects = load_rubric_aspects(rubric_path)
    aspect = next(a for a in aspects if a.id == "code-quality")

    brief_path = build_brief(
        aspect,
        workspace=workspace,
        topic="FastAPI",
        skill_content="# Modern Python\n\nUse uv and ruff.",
        skill_name="modern-python",
    )

    content = brief_path.read_text(encoding="utf-8")
    assert "## Экспертный контекст (навык: modern-python)" in content
    assert "Use uv and ruff." in content


def test_build_brief_writes_file(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "code-index.md").write_text(
        "# Code Index\n\n## Tree\n\n- `README.md` (10 lines)\n- `main.py` (20 lines)\n",
        encoding="utf-8",
    )
    aspects = load_rubric_aspects(
        Path(__file__).resolve().parents[1] / "mentor" / "config" / "rubrics" / "default.yaml",
    )
    aspect = aspects[0]

    brief_path = build_brief(aspect, workspace=workspace, topic="CLI-утилита")

    assert brief_path.exists()
    content = brief_path.read_text(encoding="utf-8")
    assert "code/" in content
    assert "code/README.md" in content
    assert f"review-{aspect.id}.md" in content


def test_select_files_for_documentation_includes_readme(tmp_path: Path) -> None:
    code_index = tmp_path / "code-index.md"
    code_index.write_text(
        "# Code Index\n\n## Tree\n\n- `README.md` (10 lines)\n- `main.py` (20 lines)\n",
        encoding="utf-8",
    )

    files = select_files_for_aspect("documentation", code_index)

    assert "code/README.md" in files


def test_resolve_aspect_id_normalizes_underscore(tmp_path: Path) -> None:
    rubric = tmp_path / "rubric.md"
    rubric.write_text(
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("mentor", "config", "rubrics", "default.yaml")
        .read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    assert resolve_aspect_id("code_quality", rubric) == "code-quality"
    assert resolve_aspect_id("error_handling", rubric) == "error-handling"


def test_resolve_aspect_id_rejects_unknown(tmp_path: Path) -> None:
    rubric = tmp_path / "rubric.md"
    rubric.write_text(
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("mentor", "config", "rubrics", "default.yaml")
        .read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(BriefError, match="неизвестный aspect-id"):
        resolve_aspect_id("typo-aspect", rubric)
