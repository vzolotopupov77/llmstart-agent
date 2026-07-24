"""Smoke E2E: CLI check без реального LLM (mock OpenRouter + orchestrator)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from mentor.cli import app
from mentor.config import AppConfig
from mentor.parser import Submission


def _write_smoke_artifacts(workspace: Path) -> None:
    (workspace / "notes").mkdir(parents=True, exist_ok=True)
    (workspace / "plan.md").write_text("# plan\n", encoding="utf-8")
    (workspace / "feedback.md").write_text(
        "## Хорошо\n\n- Структура CLI понятна.\n\n"
        "## Обязательно исправить\n\n"
        "- `code/main.py`: нет обработки invalid args.\n",
        encoding="utf-8",
    )
    (workspace / "fix_plan.md").write_text(
        "[Высокий] main.py — добавить валидацию аргументов\n",
        encoding="utf-8",
    )
    (workspace / "notes" / "review-cli-design.md").write_text("ok\n", encoding="utf-8")


def _fake_run_orchestrator(
    submission: Submission,
    workspace: Path,
    config: AppConfig,
    **kwargs: object,
) -> None:
    del submission, config, kwargs
    _write_smoke_artifacts(workspace)


def _make_fixture_project(tmp_path: Path) -> Path:
    source = tmp_path / "student-cli"
    source.mkdir()
    (source / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (source / "README.md").write_text("# Student CLI\n", encoding="utf-8")
    (source / "workspace").mkdir()
    (source / "workspace" / "nested.md").write_text("skip\n", encoding="utf-8")
    return source


def test_check_smoke_e2e_compact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _make_fixture_project(tmp_path)
    workspace = tmp_path / "ws"
    workspace.mkdir()

    monkeypatch.setattr("mentor.cli.tempfile.mkdtemp", lambda **_kw: str(workspace))

    with (
        patch(
            "mentor.cli.check_openrouter_connection",
            return_value=(True, "соединение установлено"),
        ),
        patch("mentor.cli.run_orchestrator", side_effect=_fake_run_orchestrator),
    ):
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["check", str(source), "CLI-утилита на Python", "--compact"],
        )

    assert result.exit_code == 0, result.stdout
    assert "OpenRouter: соединение установлено" in result.stdout
    assert "Feedback" in result.stdout
    assert "main.py" in result.stdout
    assert (workspace / "code" / "main.py").exists()
    assert not (workspace / "code" / "workspace").exists()


def test_check_smoke_e2e_verbose(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _make_fixture_project(tmp_path)
    workspace = tmp_path / "ws-verbose"
    workspace.mkdir()

    monkeypatch.setattr("mentor.cli.tempfile.mkdtemp", lambda **_kw: str(workspace))

    with (
        patch(
            "mentor.cli.check_openrouter_connection",
            return_value=(True, "соединение установлено"),
        ),
        patch("mentor.cli.run_orchestrator", side_effect=_fake_run_orchestrator),
    ):
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["check", str(source), "CLI-утилита на Python", "--verbose"],
        )

    assert result.exit_code == 0, result.stdout
    assert "Context limit:" in result.stdout
    assert "Workspace:" in result.stdout
