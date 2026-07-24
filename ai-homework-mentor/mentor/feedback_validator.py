"""Валидация feedback против code-index.md."""

from __future__ import annotations

import re
from pathlib import Path

README_ABSENCE_PATTERNS = (
    re.compile(r"readme\s+(?:отсутствует|не\s+найден|не\s+обнаружен|missing)", re.IGNORECASE),
    re.compile(r"(?:нет|отсутствует|не\s+создан)\s+readme", re.IGNORECASE),
    re.compile(r"отсутствует\s+(?:файл\s+)?readme", re.IGNORECASE),
    re.compile(r"readme\.md\s+(?:отсутствует|missing|not\s+found)", re.IGNORECASE),
)


def parse_code_index_paths(code_index_path: Path) -> set[str]:
    """Извлечь пути файлов из code-index.md (относительно code/)."""
    if not code_index_path.exists():
        return set()
    paths: set[str] = set()
    for line in code_index_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- `([^`]+)`", line.strip())
        if match:
            paths.add(match.group(1).replace("\\", "/"))
    return paths


def _line_claims_missing_readme(line: str) -> bool:
    if any(pattern.search(line) for pattern in README_ABSENCE_PATTERNS):
        return True
    normalized = line.lower()
    if "readme" not in normalized:
        return False
    return any(
        phrase in normalized
        for phrase in (
            "добавить readme",
            "add readme",
            "создать readme",
            "create readme",
            "написать readme",
        )
    )


def _filter_section_lines(lines: list[str], *, indexed_paths: set[str]) -> list[str]:
    readme_present = any(path.lower() == "readme.md" for path in indexed_paths)
    if not readme_present:
        return lines
    return [line for line in lines if not _line_claims_missing_readme(line)]


def _rewrite_section(text: str, heading: str, *, indexed_paths: set[str]) -> str:
    pattern = rf"^(#{{1,2}}\s*{re.escape(heading)}\s*\n)(.*?)(?=^#{{1,2}}\s|\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if match is None:
        return text

    header = match.group(1)
    body = match.group(2)
    body_lines = body.splitlines(keepends=True)
    content_lines = [line for line in body_lines if line.strip()]
    filtered = _filter_section_lines(content_lines, indexed_paths=indexed_paths)
    if filtered == content_lines:
        return text

    if not filtered:
        filtered = ["- (пункт удалён валидатором: README есть в code-index.md)\n"]

    new_body = "".join(filtered)
    if not new_body.endswith("\n"):
        new_body += "\n"
    return text[: match.start()] + header + new_body + text[match.end() :]


def validate_feedback_artifacts(workspace: Path) -> bool:
    """Сверить claims об отсутствии файлов с code-index; правит feedback.md и fix_plan.md.

    Returns:
        True если были внесены изменения.

    """
    code_index = workspace / "code-index.md"
    feedback_path = workspace / "feedback.md"
    fix_plan_path = workspace / "fix_plan.md"
    if not code_index.exists() or not feedback_path.exists():
        return False

    indexed_paths = parse_code_index_paths(code_index)
    if not indexed_paths:
        return False

    feedback_text = feedback_path.read_text(encoding="utf-8")
    updated_feedback = _rewrite_section(
        feedback_text,
        "Обязательно исправить",
        indexed_paths=indexed_paths,
    )
    updated_feedback = _rewrite_section(
        updated_feedback,
        "Исправить",
        indexed_paths=indexed_paths,
    )

    changed = updated_feedback != feedback_text
    if changed:
        feedback_path.write_text(updated_feedback, encoding="utf-8")

    if fix_plan_path.exists():
        fix_text = fix_plan_path.read_text(encoding="utf-8")
        fix_lines = fix_text.splitlines(keepends=True)
        filtered_fix = _filter_section_lines(fix_lines, indexed_paths=indexed_paths)
        if filtered_fix != fix_lines:
            fix_plan_path.write_text("".join(filtered_fix), encoding="utf-8")
            changed = True

    return changed
