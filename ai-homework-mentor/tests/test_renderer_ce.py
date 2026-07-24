"""Тесты CE-статистики verbose renderer."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from mentor.events import (
    CompactionEvent,
    PlanEvent,
    SkillEvent,
    SummarizationEvent,
    TopicDetectedEvent,
)
from mentor.renderer import VerboseRenderer


def test_summarization_dedupe_by_key() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(console=console, context_limit=128_000)
    event = SummarizationEvent(
        tokens_before=9_000,
        tokens_after=1_250,
        trigger_percent=7,
        context_limit=128_000,
        history_file="/conversation_history/t.md",
        dedupe_key="5:/conversation_history/t.md",
    )
    renderer.on_summarization(event)
    renderer.on_summarization(event)

    assert len(renderer.summarization_rows) == 1


def test_ce_summary_does_not_sum_summarization_savings() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(console=console, context_limit=128_000)
    for cutoff in (3, 8, 12):
        renderer.on_summarization(
            SummarizationEvent(
                tokens_before=9_000,
                tokens_after=1_250,
                trigger_percent=7,
                context_limit=128_000,
                dedupe_key=f"{cutoff}:/conversation_history/t.md",
            ),
        )

    summary = renderer._format_ce_summary()  # noqa: SLF001

    assert "3× middleware" in summary
    assert "1 поток" in summary
    assert "~7,750" in summary or "~7750" in summary
    assert "205" not in summary
    assert "160%" not in summary


def test_ce_summary_skips_zero_token_garbage() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(
        console=console,
        context_limit=128_000,
        summarization_threshold=5_000,
    )
    renderer.on_summarization(
        SummarizationEvent(
            tokens_before=0,
            tokens_after=1,
            trigger_percent=0,
            context_limit=128_000,
            dedupe_key="0:/conversation_history/t.md",
        ),
    )
    renderer.on_summarization(
        SummarizationEvent(
            tokens_before=9_000,
            tokens_after=1_250,
            trigger_percent=7,
            context_limit=128_000,
            dedupe_key="5:/conversation_history/t.md",
        ),
    )

    summary = renderer._format_ce_summary()  # noqa: SLF001

    assert len(renderer.summarization_rows) == 2
    assert "2× middleware" in summary


def test_ce_summary_does_not_sum_compaction_savings() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(console=console, context_limit=12_000)
    for cutoff in range(14):
        renderer.on_compaction(
            CompactionEvent(
                tokens_before=10_500,
                tokens_after=2_500,
                trigger="окно достигло ≥85% context_limit (10,200 / 12,000 токенов)",
                context_limit=12_000,
                dedupe_key=f"{cutoff}:/conversation_history/t.md",
            ),
        )

    summary = renderer._format_ce_summary()  # noqa: SLF001

    assert "14× middleware" in summary
    assert "~8,000" in summary or "~8000" in summary
    assert "10,200" in summary
    assert "119" not in summary
    assert "999%" not in summary


def test_reset_after_topic_change_clears_plan_and_skills() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(console=console, context_limit=128_000)
    renderer.skill_rows.append(
        SkillEvent(aspect="structure", skill_name=None, skill_found=False),
    )
    renderer._todos = [{"content": "Структура проекта", "status": "completed"}]  # noqa: SLF001
    renderer._shown_plan_keys = {"Структура проекта|completed"}  # noqa: SLF001
    renderer._last_rendered_plan_len = 1  # noqa: SLF001
    renderer._plan_panel_shown = True  # noqa: SLF001

    renderer.on_topic_detected(TopicDetectedEvent(topic="CLI", source="user"))

    assert renderer.skill_rows == []
    assert renderer._todos == []  # noqa: SLF001
    assert renderer._shown_plan_keys == set()  # noqa: SLF001
    assert renderer._last_rendered_plan_len == 0  # noqa: SLF001
    assert renderer._plan_panel_shown is False  # noqa: SLF001


def test_plan_update_shows_completed_steps() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(console=console, context_limit=128_000)

    renderer.on_plan_update(
        PlanEvent(
            step="Проверить аспект cli-design",
            status="completed",
            index=2,
            total=7,
        ),
    )
    renderer.on_plan_update(
        PlanEvent(
            step="Проверить аспект code-quality",
            status="in_progress",
            index=3,
            total=7,
        ),
    )

    output = console.file.getvalue()
    assert "[2/7] Проверить аспект cli-design" in output
    assert "[3/7] Проверить аспект code-quality" in output
    assert "●" in output or "in_progress" in output


def test_plan_panel_refreshes_when_todos_grow() -> None:
    console = Console(file=StringIO(), width=120, force_terminal=True)
    renderer = VerboseRenderer(console=console, context_limit=128_000)

    renderer.on_plan_update(
        PlanEvent(step="Подготовить plan.md", status="in_progress", index=1, total=1),
    )
    renderer.on_plan_update(
        PlanEvent(step="Подготовить plan.md", status="completed", index=1, total=3),
    )
    renderer.on_plan_update(
        PlanEvent(step="Проверить cli-design", status="pending", index=2, total=3),
    )
    renderer.on_plan_update(
        PlanEvent(step="Синтез feedback", status="pending", index=3, total=3),
    )

    output = console.file.getvalue()
    assert "План проверки" in output
    assert "cli-design" in output
    assert "Синтез feedback" in output
