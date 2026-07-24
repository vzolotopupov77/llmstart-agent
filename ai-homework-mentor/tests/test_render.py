"""Тесты рендеринга feedback."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from mentor.render import _extract_section, _parse_fix_plan_lines, render_user_question

FEEDBACK_H2 = """\
## Хорошо

### Структура проекта
- Проект хорошо организован.
- Файлы разумного размера.

## Обязательно исправить

- Нет критических ошибок.

## Рекомендации

- Улучшить типизацию.
"""

FEEDBACK_H3_UNDER_INTRO = """\
## Общая оценка

Краткий вводный абзац.

---

### Хорошо

- **Структура проекта**: хорошо организован.
- **Документация**: README подробный.

### Обязательно исправить

- **Типизация**: недостаточная в agent.py.

### Рекомендации

- Добавить docstring.
"""


def test_extract_section_h2_with_subsections() -> None:
    good = _extract_section(FEEDBACK_H2, "Хорошо")
    assert len(good) == 2
    assert good[0].startswith("Структура проекта:")
    assert "организован" in good[0]

    must_fix = _extract_section(FEEDBACK_H2, "Обязательно исправить", "Исправить")
    assert len(must_fix) == 1
    assert "критических" in must_fix[0].casefold()


def test_extract_section_h3_after_intro() -> None:
    good = _extract_section(FEEDBACK_H3_UNDER_INTRO, "Хорошо")
    assert len(good) == 2
    assert "Структура проекта" in good[0]
    assert "README" in good[1]

    must_fix = _extract_section(FEEDBACK_H3_UNDER_INTRO, "Обязательно исправить")
    assert len(must_fix) == 1
    assert "Типизация" in must_fix[0]


def test_extract_section_chto_khorosho_heading() -> None:
    text = """\
## Что хорошо

- Чёткое SoC между модулями.
- Fail-fast конфигурация.

## Обязательно исправить

- agent.py: bare except.
"""
    good = _extract_section(text, "Хорошо", "Что хорошо")
    assert len(good) == 2
    assert "SoC" in good[0]


def test_parse_fix_plan_lines_includes_priority_headings() -> None:
    text = """\
### [Высокий] CLI tests
- Добавить тест --help

### [Средний] Docs
- Расширить README
"""
    lines = _parse_fix_plan_lines(text)
    assert lines[0] == "[Высокий] CLI tests"
    assert any("Добавить тест --help" in line for line in lines)
    assert "[Средний] Docs" in lines


def test_render_user_question_verbose_skips_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Регрессия: в verbose панель уже показана через UserQuestionEvent."""
    buffer = StringIO()
    test_console = Console(file=buffer, force_terminal=False, width=120)
    monkeypatch.setattr(
        "mentor.render.typer.prompt",
        lambda _label: "FastAPI",
    )

    answer = render_user_question(
        test_console,
        "Какой тип проекта?",
        show_panel=False,
    )

    assert answer == "FastAPI"
    rendered = buffer.getvalue()
    assert "Уточняющий вопрос" not in rendered
    assert "Какой тип проекта?" not in rendered


def test_render_user_question_compact_shows_panel(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = StringIO()
    test_console = Console(file=buffer, force_terminal=False, width=120)
    monkeypatch.setattr(
        "mentor.render.typer.prompt",
        lambda _label: "CLI",
    )

    answer = render_user_question(test_console, "Тип проекта?")

    assert answer == "CLI"
    rendered = buffer.getvalue()
    assert "Уточняющий вопрос" in rendered
    assert "Тип проекта?" in rendered
