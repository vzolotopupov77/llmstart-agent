"""Unit-тесты orchestrator-агента."""

from __future__ import annotations

from pathlib import Path

from mentor.agent import (
    AgentRunContext,
    _artifact_error_message,
    _build_continue_message,
    _missing_artifacts,
    _next_orchestrator_action,
    _recursion_limit_error_message,
    _spawn_reviewer_impl,
)
from mentor.config import AppConfig
from mentor.parser import Submission


def test_missing_artifacts_detects_feedback(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "plan.md").write_text("# plan", encoding="utf-8")

    missing = _missing_artifacts(workspace)

    assert "feedback.md" in missing
    assert "fix_plan.md" in missing
    assert "notes/review-*.md" in missing


def test_missing_artifacts_empty_when_complete(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "notes").mkdir(parents=True)
    for name in ("plan.md", "feedback.md", "fix_plan.md"):
        (workspace / name).write_text(name, encoding="utf-8")
    (workspace / "notes" / "review-structure.md").write_text("ok", encoding="utf-8")

    assert _missing_artifacts(workspace) == []


def test_artifact_error_message_lists_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    message = _artifact_error_message(workspace)
    assert "feedback.md" in message
    assert "MODEL" in message


def test_recursion_limit_error_message_includes_stats(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "code-index.md").write_text(
        "# Code Index\n\n- **files:** 442\n- **lines:** ~47,445\n",
        encoding="utf-8",
    )
    (workspace / "notes").mkdir()
    (workspace / "notes" / "review-structure.md").write_text("ok", encoding="utf-8")

    message = _recursion_limit_error_message(workspace, limit=200)

    assert "200" in message
    assert "442" in message
    assert "47,445" in message
    assert "review-нот: 1" in message
    assert "AGENT_RECURSION_LIMIT" in message


def test_next_orchestrator_action_points_to_missing_aspect(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "notes").mkdir(parents=True)
    (workspace / "rubric.md").write_text(
        "aspects:\n"
        "  - id: cli-design\n    name: Дизайн CLI\n"
        "  - id: testing\n    name: Тестирование\n",
        encoding="utf-8",
    )
    (workspace / "notes" / "review-cli-design.md").write_text("done", encoding="utf-8")

    action = _next_orchestrator_action(workspace)

    assert "spawn_reviewer" in action
    assert "brief-testing.md" in action


def test_next_orchestrator_action_synthesis_when_all_notes_done(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "notes").mkdir(parents=True)
    (workspace / "rubric.md").write_text(
        "aspects:\n  - id: cli-design\n    name: Дизайн CLI\n",
        encoding="utf-8",
    )
    (workspace / "notes" / "review-cli-design.md").write_text("done", encoding="utf-8")

    action = _next_orchestrator_action(workspace)

    assert "feedback.md" in action
    assert "spawn_reviewer запрещён" in action


def test_build_continue_message_includes_plan_rebuild_hint(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()

    message = _build_continue_message(workspace, plan_needs_rebuild=True)

    assert "Старый plan.md удалён" in message
    assert "только по аспектам текущей рубрики" in message


def test_build_continue_message_includes_next_action(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "notes").mkdir(parents=True)
    (workspace / "rubric.md").write_text(
        "aspects:\n  - id: cli-design\n    name: Дизайн CLI\n",
        encoding="utf-8",
    )

    message = _build_continue_message(workspace)

    assert "spawn_reviewer" in message
    assert "brief-cli-design.md" in message


def test_spawn_reviewer_missing_brief_returns_soft_error(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "briefs").mkdir()
    config = AppConfig(openrouter_api_key="test-key")
    submission = Submission(source_type="local", source="/tmp", topic="CLI")
    ctx = AgentRunContext(workspace=workspace, config=config, submission=submission)

    result = _spawn_reviewer_impl("briefs/brief-structure.md", ctx)

    assert "бриф не найден" in result
    assert "write_file" in result
