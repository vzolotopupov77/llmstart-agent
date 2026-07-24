"""Рендеринг фидбэка и прогресса проверки."""

from __future__ import annotations

import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

STATUS_ICONS = {
    "completed": "[green]✓[/green]",
    "in_progress": "[yellow]→[/yellow]",
    "pending": "[dim]○[/dim]",
}


def render_submission_summary(
    console: Console,
    *,
    topic: str | None,
    source_label: str,
    file_count: int,
    line_count: int,
) -> None:
    """Показать краткую сводку по входу."""
    topic_text = topic or "не указана"
    console.print(f"📋 Тема:    {topic_text}")
    console.print(
        f"📁 Код:     {source_label} ({file_count} файлов, ~{line_count:,} строк)",
    )
    console.print()


def render_todo_progress(
    console: Console,
    todos: list[dict[str, str]],
    *,
    last_rendered: set[str] | None = None,
) -> set[str]:
    """Отрисовать новые/изменённые шаги плана."""
    rendered = last_rendered or set()
    total = len(todos)
    for index, todo in enumerate(todos, start=1):
        content = todo.get("content", "").strip()
        status = todo.get("status", "pending")
        key = f"{content}|{status}"
        if key in rendered:
            continue
        rendered.add(key)
        icon = STATUS_ICONS.get(status, STATUS_ICONS["pending"])
        console.print(f"  {icon} [{index}/{total}] {content}")
    return rendered


def _parse_heading(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())
    if match is None:
        return None
    return len(match.group(1)), match.group(2).strip()


def _find_section_start(lines: list[str], heading: str) -> tuple[int, int] | None:
    for index, line in enumerate(lines):
        parsed = _parse_heading(line)
        if parsed is None:
            continue
        level, title = parsed
        if title.casefold() == heading.casefold():
            return index + 1, level
    return None


def _normalize_section_line(line: str, subsection: str | None) -> str | None:
    stripped = line.strip()
    if not stripped or stripped == "---":
        return None
    item = stripped.lstrip("-•*").strip() if stripped.startswith(("-", "•", "*")) else stripped
    if subsection:
        return f"{subsection}: {item}"
    return item


def _collect_section_items(lines: list[str], start_idx: int, section_level: int) -> list[str]:
    items: list[str] = []
    subsection: str | None = None
    for line in lines[start_idx:]:
        parsed = _parse_heading(line)
        if parsed is not None:
            level, title = parsed
            if level <= section_level:
                break
            subsection = title
            continue

        item = _normalize_section_line(line, subsection)
        if item is not None:
            items.append(item)
    return items


def _extract_section(text: str, *headings: str) -> list[str]:
    """Извлечь пункты секции feedback по заголовку (# … ######)."""
    lines = text.splitlines()
    for heading in headings:
        found = _find_section_start(lines, heading)
        if found is None:
            continue
        start_idx, section_level = found
        items = _collect_section_items(lines, start_idx, section_level)
        if items:
            return items
    return []


def _parse_code_index_stats(code_index_path: Path) -> tuple[int, int]:
    if not code_index_path.exists():
        return 0, 0
    text = code_index_path.read_text(encoding="utf-8")
    files_match = re.search(r"\*\*files:\*\*\s*(\d+)", text)
    lines_match = re.search(r"\*\*lines:\*\*\s*~?([\d,]+)", text)
    file_count = int(files_match.group(1)) if files_match else 0
    line_count = int(lines_match.group(1).replace(",", "")) if lines_match else 0
    return file_count, line_count


def _parse_fix_plan_lines(fix_plan_text: str) -> list[str]:
    lines: list[str] = []
    for line in fix_plan_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                lines.append(heading)
            continue
        lines.append(stripped)
    return lines


def render_feedback_panel(console: Console, workspace: Path) -> None:
    """Отрисовать итоговый Feedback + Fix Plan из workspace."""
    feedback_path = workspace / "feedback.md"
    fix_plan_path = workspace / "fix_plan.md"

    feedback_text = feedback_path.read_text(encoding="utf-8") if feedback_path.exists() else ""
    fix_plan_text = fix_plan_path.read_text(encoding="utf-8") if fix_plan_path.exists() else ""

    good_items = _extract_section(feedback_text, "Хорошо", "Что хорошо")
    must_fix_items = _extract_section(
        feedback_text,
        "Обязательно исправить",
        "Исправить",
    )

    fix_plan_lines = _parse_fix_plan_lines(fix_plan_text)

    body_lines: list[str] = ["", "  ✅  Хорошо"]
    if good_items:
        body_lines.extend(f"  • {item.lstrip('-•').strip()}" for item in good_items)
    else:
        body_lines.append("  • (нет явных сильных сторон)")

    body_lines.extend(["", "  ⚠️   Обязательно исправить"])
    if must_fix_items:
        for index, item in enumerate(must_fix_items, start=1):
            body_lines.append(f"  {index}.  {item.lstrip('-•0123456789. ').strip()}")
    else:
        body_lines.append("  1.  (замечания не найдены)")

    body_lines.extend(["", "  📋  Fix Plan"])
    if fix_plan_lines:
        body_lines.extend(f"  {line.lstrip('-•').strip()}" for line in fix_plan_lines)
    else:
        body_lines.append("  (план исправлений пуст)")

    console.print(
        Panel(
            "\n".join(body_lines),
            title="Feedback",
            border_style="green",
        ),
    )


def render_user_question(
    console: Console,
    question: str,
    *,
    show_panel: bool = True,
) -> str:
    """Показать уточняющий вопрос и прочитать ответ из stdin.

    В verbose панель уже выведена через UserQuestionEvent — show_panel=False.
    """
    if show_panel:
        console.print()
        console.print(
            Panel(
                question,
                title="Уточняющий вопрос",
                border_style="yellow",
            ),
        )
    return str(typer.prompt("  Ваш ответ"))


def read_code_index_stats(workspace: Path) -> tuple[int, int]:
    """Прочитать статистику из code-index.md."""
    return _parse_code_index_stats(workspace / "code-index.md")
