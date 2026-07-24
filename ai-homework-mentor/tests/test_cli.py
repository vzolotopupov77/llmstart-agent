"""Тесты CLI: справка и обработка некорректных аргументов."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from mentor.cli import app

runner = CliRunner()


def test_root_help_shows_usage() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "AI Homework Mentor" in result.stdout
    assert "check" in result.stdout


def test_check_help_shows_options() -> None:
    result = runner.invoke(app, ["check", "--help"])

    assert result.exit_code == 0
    assert "Проверить домашнее задание по рубрике" in result.stdout
    assert "--verbose" in result.stdout
    assert "--compact" in result.stdout
    assert "GitHub-ссылка или локальный путь" in result.stdout


def test_check_missing_source_argument() -> None:
    result = runner.invoke(app, ["check"])

    assert result.exit_code == 2
    assert "Missing argument" in result.output
    assert "SOURCE" in result.output


def test_check_empty_source_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with patch(
        "mentor.cli.check_openrouter_connection",
        return_value=(True, "соединение установлено"),
    ):
        result = runner.invoke(app, ["check", "", "CLI-утилита"])

    assert result.exit_code == 1
    assert "✗" in result.stdout
    assert "Вход пустой" in result.stdout


def test_check_unknown_local_path_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    missing = tmp_path / "does-not-exist"

    with patch(
        "mentor.cli.check_openrouter_connection",
        return_value=(True, "соединение установлено"),
    ):
        result = runner.invoke(app, ["check", str(missing), "CLI-утилита"])

    assert result.exit_code == 1
    assert "✗" in result.stdout
    assert "Не удалось распознать вход" in result.stdout


def test_check_file_instead_of_directory_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    file_path = tmp_path / "not-a-dir.txt"
    file_path.write_text("x", encoding="utf-8")

    with patch(
        "mentor.cli.check_openrouter_connection",
        return_value=(True, "соединение установлено"),
    ):
        result = runner.invoke(app, ["check", str(file_path), "CLI-утилита"])

    assert result.exit_code == 1
    assert "✗" in result.stdout
    assert "не является директорией" in result.stdout


def test_check_openrouter_failure_exits_with_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "bad-key")
    source = tmp_path / "project"
    source.mkdir()

    with patch(
        "mentor.cli.check_openrouter_connection",
        return_value=(False, "Invalid API key"),
    ):
        result = runner.invoke(app, ["check", str(source), "CLI-утилита"])

    assert result.exit_code == 1
    assert "✗ OpenRouter: Invalid API key" in result.stdout
