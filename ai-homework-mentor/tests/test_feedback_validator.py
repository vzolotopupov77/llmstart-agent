"""Тесты валидации feedback против code-index."""

from __future__ import annotations

from pathlib import Path

from mentor.feedback_validator import parse_code_index_paths, validate_feedback_artifacts


def test_parse_code_index_paths(tmp_path: Path) -> None:
    code_index = tmp_path / "code-index.md"
    code_index.write_text(
        "# Code Index\n\n## Tree\n\n- `README.md` (10 lines)\n- `main.py` (50 lines)\n",
        encoding="utf-8",
    )

    assert parse_code_index_paths(code_index) == {"README.md", "main.py"}


def test_validator_removes_false_readme_claim(tmp_path: Path) -> None:
    workspace = tmp_path
    (workspace / "code-index.md").write_text(
        "# Code Index\n\n## Tree\n\n- `README.md` (10 lines)\n",
        encoding="utf-8",
    )
    (workspace / "feedback.md").write_text(
        "# Feedback\n\n## Хорошо\n\n- Есть структура\n\n"
        "## Обязательно исправить\n\n"
        "- README отсутствует в корне проекта\n"
        "- Нет обработки ошибок\n",
        encoding="utf-8",
    )
    (workspace / "fix_plan.md").write_text(
        "# Fix Plan\n\n1. Добавить README\n2. Исправить ошибки\n",
        encoding="utf-8",
    )

    changed = validate_feedback_artifacts(workspace)
    assert changed is True

    feedback = (workspace / "feedback.md").read_text(encoding="utf-8")
    assert "README отсутствует" not in feedback
    assert "обработки ошибок" in feedback

    fix_plan = (workspace / "fix_plan.md").read_text(encoding="utf-8")
    assert "Добавить README" not in fix_plan
    assert "Исправить ошибки" in fix_plan
