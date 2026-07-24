"""Unit-тесты Reviewer-субагента."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mentor.brief import build_brief, load_default_aspects
from mentor.config import AppConfig
from mentor.reviewer import (
    ReviewerError,
    _locate_review_note,
    run_reviewer,
)


@pytest.fixture
def config() -> AppConfig:
    return AppConfig(openrouter_api_key="test-key")


def test_run_reviewer_missing_brief(tmp_path: Path, config: AppConfig) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()

    with pytest.raises(ReviewerError, match="бриф не найден"):
        run_reviewer(Path("briefs/brief-structure.md"), workspace, config)


@patch("mentor.reviewer.create_deep_agent")
def test_run_reviewer_success(
    mock_create_agent: MagicMock,
    tmp_path: Path,
    config: AppConfig,
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "code-index.md").write_text("# index\n", encoding="utf-8")
    rubric_source = (
        Path(__file__).resolve().parents[1] / "mentor" / "config" / "rubrics" / "default.yaml"
    )
    rubric_text = rubric_source.read_text(encoding="utf-8")
    (workspace / "rubric.md").write_text(rubric_text, encoding="utf-8")

    aspect = load_default_aspects()[0]
    brief_path = build_brief(aspect, workspace=workspace, topic="CLI")

    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {
        "messages": [],
    }
    mock_create_agent.return_value = mock_agent

    notes_dir = workspace / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_path = notes_dir / f"review-{aspect.id}.md"
    note_path.write_text(
        "## findings\n- ok\n\n## recommendations\n- none\n",
        encoding="utf-8",
    )

    result = run_reviewer(brief_path, workspace, config)

    assert result.aspect == aspect.id
    assert result.note_path == Path("notes") / f"review-{aspect.id}.md"
    mock_agent.invoke.assert_called_once()


def test_locate_review_note_finds_underscore_variant(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    notes_dir = workspace / "notes"
    notes_dir.mkdir(parents=True)
    note = notes_dir / "review-code_quality.md"
    note.write_text("## findings\n- ok\n\n## recommendations\n- fix\n", encoding="utf-8")

    located = _locate_review_note(workspace, "code-quality")

    assert located == Path("notes/review-code_quality.md")


@patch("mentor.reviewer.create_deep_agent")
def test_run_reviewer_retries_until_note_created(
    mock_create_agent: MagicMock,
    tmp_path: Path,
    config: AppConfig,
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    rubric_source = (
        Path(__file__).resolve().parents[1] / "mentor" / "config" / "rubrics" / "default.yaml"
    )
    (workspace / "rubric.md").write_text(
        rubric_source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (workspace / "code-index.md").write_text("# index\n", encoding="utf-8")

    aspect = load_default_aspects()[0]
    brief_path = build_brief(aspect, workspace=workspace, topic="CLI")

    mock_agent = MagicMock()
    mock_create_agent.return_value = mock_agent

    notes_dir = workspace / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    call_count = {"value": 0}

    def invoke_side_effect(*_args: object, **_kwargs: object) -> dict[str, list[object]]:
        call_count["value"] += 1
        if call_count["value"] >= 2:
            (notes_dir / f"review-{aspect.id}.md").write_text(
                "## findings\n- ok\n\n## recommendations\n- none\n",
                encoding="utf-8",
            )
        return {"messages": []}

    mock_agent.invoke.side_effect = invoke_side_effect

    result = run_reviewer(brief_path, workspace, config)

    assert result.aspect == aspect.id
    assert mock_agent.invoke.call_count == 2
