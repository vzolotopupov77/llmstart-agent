"""Rich verbose-рендеринг событий агента."""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mentor.ce import compaction_overflow_threshold
from mentor.events import (
    AgentEvent,
    CompactionEvent,
    ContextEvent,
    FileEvent,
    FileOffloadEvent,
    PlanEvent,
    RubricSelectedEvent,
    SkillEvent,
    SubagentEndEvent,
    SubagentStartEvent,
    SummarizationEvent,
    TopicDetectedEvent,
    UserQuestionEvent,
)
from mentor.tracker import is_outside_student_code

PLAN_STATUS_ICONS = {
    "completed": "✓",
    "in_progress": "●",
    "pending": "○",
}


@dataclass
class VerboseRenderer:
    """Verbose-вывод: план, файлы, субагенты, рост контекста, итоговая панель."""

    console: Console
    context_limit: int
    summarization_threshold: int = 80_000
    context_rows: list[ContextEvent] = field(default_factory=list)
    subagent_rows: list[SubagentEndEvent] = field(default_factory=list)
    file_offload_rows: list[FileOffloadEvent] = field(default_factory=list)
    summarization_rows: list[SummarizationEvent] = field(default_factory=list)
    compaction_rows: list[CompactionEvent] = field(default_factory=list)
    skill_rows: list[SkillEvent] = field(default_factory=list)
    _seen_ce_keys: set[str] = field(default_factory=set)
    _todos: list[dict[str, str]] = field(default_factory=list)
    _shown_plan_keys: set[str] = field(default_factory=set)
    _last_rendered_plan_len: int = 0
    _plan_panel_shown: bool = False

    def handle(self, event: AgentEvent) -> None:
        """Маршрутизация события в соответствующий обработчик."""
        if isinstance(event, PlanEvent):
            self.on_plan_update(event)
        elif isinstance(event, FileEvent):
            self.on_file_event(event)
        elif isinstance(event, SubagentStartEvent):
            self.on_subagent_start(event)
        elif isinstance(event, SubagentEndEvent):
            self.on_subagent_end(event)
        elif isinstance(event, FileOffloadEvent):
            self.on_file_offload(event)
        elif isinstance(event, SummarizationEvent):
            self.on_summarization(event)
        elif isinstance(event, CompactionEvent):
            self.on_compaction(event)
        elif isinstance(event, ContextEvent):
            self.on_context_event(event)
        elif isinstance(event, SkillEvent):
            self.on_skill(event)
        elif isinstance(event, TopicDetectedEvent):
            self.on_topic_detected(event)
        elif isinstance(event, RubricSelectedEvent):
            self.on_rubric_selected(event)
        elif isinstance(event, UserQuestionEvent):
            self.on_user_question(event)

    def on_topic_detected(self, event: TopicDetectedEvent) -> None:
        """Показать определённую тему."""
        if event.source == "user":
            self.reset_after_topic_change()
        source_label = {
            "cli": "указана в CLI",
            "auto": "определена автоматически",
            "user": "уточнена пользователем",
        }.get(event.source, event.source)
        self.console.print(f"\n  📋 Тема: {event.topic} ({source_label})")

    def reset_after_topic_change(self) -> None:
        """Сбросить план и навыки после смены рубрики через HITL."""
        self._todos = []
        self._shown_plan_keys = set()
        self._last_rendered_plan_len = 0
        self._plan_panel_shown = False
        self.skill_rows = []

    def on_rubric_selected(self, event: RubricSelectedEvent) -> None:
        """Показать выбранную рубрику."""
        self.console.print(
            f"  📖 Рубрика: {event.rubric_file}  ({event.aspect_count} аспектов)",
        )

    def on_skill(self, event: SkillEvent) -> None:
        """Показать подключение навыка к аспекту."""
        self.skill_rows.append(event)
        if event.skill_name and event.skill_found:
            label = f'📚 Навык: {event.skill_name} → подключён к аспекту "{event.aspect}"'
        elif event.skill_name:
            label = (
                f"📚 Навык: {event.skill_name} → не найден, "
                f'аспект "{event.aspect}" (собственный промпт)'
            )
        else:
            label = f'📚 Навык: — → аспект "{event.aspect}" (собственный промпт)'
        self.console.print(f"  {label}")

    def on_user_question(self, event: UserQuestionEvent) -> None:
        """Показать уточняющий вопрос (ответ вводится через CLI callback)."""
        self.console.print()
        self.console.print(
            Panel(
                event.question,
                title="Уточняющий вопрос",
                border_style="yellow",
            ),
        )

    def on_plan_update(self, event: PlanEvent) -> None:
        """Обновить панель плана и показать прогресс шагов (in_progress / completed)."""
        self._todos = self._merge_todo(self._todos, event)
        plan_len = len(self._todos)

        should_render_panel = (
            plan_len >= 2 and plan_len != self._last_rendered_plan_len
        ) or (
            not self._plan_panel_shown and (event.total >= 2 or event.status == "in_progress")
        )
        if should_render_panel:
            self._render_plan_panel()
            self._plan_panel_shown = True
            self._last_rendered_plan_len = plan_len

        if event.status not in {"in_progress", "completed"}:
            return

        transition_key = f"{event.step}|{event.status}"
        if transition_key in self._shown_plan_keys:
            return
        self._shown_plan_keys.add(transition_key)

        icon = {
            "completed": "[green]✓[/green]",
            "in_progress": "[yellow]●[/yellow]",
        }.get(event.status, PLAN_STATUS_ICONS["pending"])
        total = event.total or plan_len or event.index
        self.console.print(f"\n  {icon} [{event.index}/{total}] {event.step}")

    def on_file_event(self, event: FileEvent) -> None:
        """Показать прочитанный файл; предупредить о пути вне code/."""
        path = event.path.replace("\\", "/")
        self.console.print(f"    📄 Прочитан: {path}")
        if is_outside_student_code(path):
            self.console.print(
                f"    [yellow]⚠[/yellow] Путь вне code/: {path}",
            )

    def on_subagent_start(self, event: SubagentStartEvent) -> None:
        """Панель запуска изолированного субагента."""
        files_line = f"  │     Файлы: {event.files_preview}" if event.files_preview else ""
        body = (
            f"  │  ← Запущен с чистым контекстом (0 токенов истории)\n"
            f"  │     Бриф: {event.brief_path}  ({event.brief_tokens:,} токенов)"
        )
        if files_line:
            body += f"\n{files_line}"
        self.console.print(
            Panel(
                body,
                title=f"Субагент: {event.aspect}-reviewer",
                border_style="green",
            ),
        )

    def on_subagent_end(self, event: SubagentEndEvent) -> None:
        """Панель завершения субагента и контраст с Sprint 03."""
        self.subagent_rows.append(event)
        self.console.print(
            Panel(
                f"  │  → Завершён\n"
                f"  │     Записал: {event.note_path}\n"
                f"  │     Контекст субагента: {event.subagent_context_tokens:,} токенов "
                f"(изолирован, не передан)",
                title=f"Субагент: {event.aspect}-reviewer",
                border_style="green",
            ),
        )
        sprint03_after = event.orchestrator_tokens_before + event.sprint03_baseline_delta
        self.console.print(
            "    "
            f"Контекст оркестратора: {event.orchestrator_tokens_before:,} → "
            f"{event.orchestrator_tokens_after:,} токенов  "
            f"(+{event.orchestrator_delta:,})",
        )
        self.console.print(
            f"    [yellow]↑[/yellow] В Sprint 03 без изоляции: "
            f"→ {sprint03_after:,} токенов (+{event.sprint03_baseline_delta:,})",
        )

    def on_file_offload(self, event: FileOffloadEvent) -> None:
        """Панель выноса объёмных данных в файл."""
        self.file_offload_rows.append(event)
        self.console.print(
            Panel(
                f"  Файл:     workspace/{event.filename}\n"
                f"  До:       {event.tokens_before:,} токенов в окне\n"
                f"  После:    {event.tokens_after:,} токенов (ссылка + саммари)\n"
                f"  Экономия: {event.savings:,} токенов",
                title="Context Engineering: Вынос в файлы",
                border_style="blue",
            ),
        )

    def on_summarization(self, event: SummarizationEvent) -> None:
        """Панель автоматической суммаризации истории."""
        if event.dedupe_key and event.dedupe_key in self._seen_ce_keys:
            return
        if event.dedupe_key:
            self._seen_ce_keys.add(event.dedupe_key)
        self.summarization_rows.append(event)
        history_line = ""
        if event.history_file:
            history_line = f"\n  Архив:    {event.history_file}"
        self.console.print(
            Panel(
                f"  Триггер:  окно достигло {event.trigger_percent}% от context_limit "
                f"({event.tokens_before:,} / {event.context_limit:,})\n"
                f"  До:       {event.tokens_before:,} токенов\n"
                f"  После:    {event.tokens_after:,} токенов (summary в контексте)\n"
                f"  Экономия: {event.savings:,} токенов"
                f"{history_line}",
                title="Context Engineering: Суммаризация истории",
                border_style="blue",
            ),
        )

    def on_compaction(self, event: CompactionEvent) -> None:
        """Панель компактизации контекста."""
        if event.dedupe_key and event.dedupe_key in self._seen_ce_keys:
            return
        if event.dedupe_key:
            self._seen_ce_keys.add(event.dedupe_key)
        self.compaction_rows.append(event)
        history_line = ""
        if event.history_file:
            history_line = f"\n  Архив:    {event.history_file}"
        self.console.print(
            Panel(
                f"  Триггер:  {event.trigger}\n"
                f"  До:       {event.tokens_before:,} токенов\n"
                f"  После:    {event.tokens_after:,} токенов (plan.md + ключевые ссылки)\n"
                f"  Экономия: {event.savings:,} токенов"
                f"{history_line}",
                title="Context Engineering: Компактизация",
                border_style="blue",
            ),
        )

    def on_context_event(self, event: ContextEvent) -> None:
        """Показать рост контекста после шага LLM."""
        self.context_rows.append(event)

        delta = event.delta
        line = (
            f"    Контекст: {event.tokens_before:,} → {event.tokens_after:,} токенов (+{delta:,})"
        )
        if event.method == "субагент" and event.sprint03_baseline_delta is not None:
            line += f"  [dim]({event.method})[/dim]"
        if event.tokens_after > self.context_limit * 0.5:
            self.console.print(f"    [red]{line.removeprefix('    ')}[/red]")
        else:
            self.console.print(line)

    def on_complete(self) -> None:
        """Итоговая панель «Контекст за сессию»."""
        if not (
            self.context_rows
            or self.subagent_rows
            or self.file_offload_rows
            or self.summarization_rows
            or self.compaction_rows
        ):
            return

        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        table.add_column("Шаг", style="white")
        table.add_column("Метод")
        table.add_column("Дельта орк.", justify="right")
        table.add_column("Экономия", justify="right")

        total_savings = 0
        if self.subagent_rows:
            for sub_row in self.subagent_rows:
                savings = sub_row.savings
                total_savings += savings
                table.add_row(
                    sub_row.aspect[:32],
                    "субагент",
                    f"+{sub_row.orchestrator_delta:,}",
                    f"-{savings:,}",
                )
        else:
            for ctx_row in self.context_rows:
                table.add_row(
                    ctx_row.step[:40],
                    ctx_row.method,
                    f"+{ctx_row.delta:,}",
                    "—",
                )

        final_tokens = self.context_rows[-1].tokens_after if self.context_rows else 0
        ratio = final_tokens / self.context_limit if self.context_limit else 0
        percent = int(ratio * 100)

        summary = Text()
        summary.append("\n")
        if self.subagent_rows:
            baseline_total = sum(row.sprint03_baseline_delta for row in self.subagent_rows)
            savings_percent = (total_savings / baseline_total * 100) if baseline_total else 0.0
            summary.append(
                f"  Итого сэкономлено: {total_savings:,} токенов "
                f"({savings_percent:.0f}% от контекста Sprint 03)\n",
            )
        summary.append(
            f"  Итого: {final_tokens:,} токенов  ({percent}% от лимита {self.context_limit:,})",
            style="bold",
        )
        summary.append("\n\n")
        if self.subagent_rows:
            summary.append("  ✓  Reviewer-субагенты изолируют детали проверки.\n")
            summary.append("     Оркестратор получает только короткий статус tool call.\n")
        else:
            summary.append("  ⚠  Субагенты не запускались — контекст растёт как в Sprint 03.\n")

        ce_lines = self._format_ce_summary()
        if ce_lines:
            summary.append("\n")
            summary.append(ce_lines)

        skills_lines = self._format_skills_summary()
        if skills_lines:
            summary.append("\n")
            summary.append(skills_lines)

        if ratio > 0.3:
            summary.stylize("yellow", 3, len(summary))

        self.console.print(
            Panel(
                Group(table, summary),
                title="📊 Контекст за сессию",
                border_style="magenta",
            ),
        )

    def _format_ce_summary(self) -> str:
        offload_savings = sum(row.savings for row in self.file_offload_rows)
        summarization_savings = (
            max((row.savings for row in self.summarization_rows), default=0)
            if self.summarization_rows
            else 0
        )
        compaction_savings = (
            max((row.savings for row in self.compaction_rows), default=0)
            if self.compaction_rows
            else 0
        )
        additive_ce = offload_savings + compaction_savings
        if additive_ce == 0 and not (
            self.file_offload_rows or self.summarization_rows or self.compaction_rows
        ):
            return ""

        lines = ["  CE-события:"]
        if self.file_offload_rows:
            lines.append(
                f"  • Вынос в файлы:    {len(self.file_offload_rows)} раз  →  "
                f"экономия {offload_savings:,} токенов",
            )
        if self.summarization_rows:
            history_files = {
                row.history_file for row in self.summarization_rows if row.history_file
            }
            threads = len(history_files) or 1
            thread_word = "поток" if threads == 1 else "потока" if threads <= 4 else "потоков"
            lines.append(
                f"  • Суммаризация:     {len(self.summarization_rows)}× middleware "
                f"({threads} {thread_word}), "
                f"~{summarization_savings:,} ток/раз при пороге {self.summarization_threshold:,}",
            )
        if self.compaction_rows:
            compaction_threshold = compaction_overflow_threshold(self.context_limit)
            lines.append(
                f"  • Компактизация:    {len(self.compaction_rows)}× middleware, "
                f"~{compaction_savings:,} ток/раз при пороге {compaction_threshold:,}",
            )
        if additive_ce > 0:
            percent = int(additive_ce / self.context_limit * 100) if self.context_limit else 0
            lines.append("  ─────────────────────────────────────────────────────────")
            lines.append(
                f"  Суммарно (вынос + компактизация): {additive_ce:,} токенов  "
                f"({percent}% от лимита)",
            )
        return "\n".join(lines) + "\n"

    def _format_skills_summary(self) -> str:
        if not self.skill_rows:
            return ""
        by_aspect: dict[str, SkillEvent] = {}
        for row in self.skill_rows:
            by_aspect[row.aspect] = row
        lines = ["  Навыки сессии:"]
        for aspect, row in by_aspect.items():
            if row.skill_name and row.skill_found:
                lines.append(f"  • {aspect}: {row.skill_name}")
            elif row.skill_name:
                lines.append(f"  • {aspect}: {row.skill_name} (не найден)")
            else:
                lines.append(f"  • {aspect}: собственный промпт")
        return "\n".join(lines) + "\n"

    def _render_plan_panel(self) -> None:
        if not self._todos:
            return
        lines: list[str] = []
        for index, todo in enumerate(self._todos, start=1):
            status = todo.get("status", "pending")
            icon = PLAN_STATUS_ICONS.get(status, PLAN_STATUS_ICONS["pending"])
            content = todo.get("content", "").strip()
            lines.append(f"  {icon} [{index}] {content}")
        self.console.print(
            Panel(
                "\n".join(lines),
                title="📋 План проверки",
                border_style="cyan",
            ),
        )

    @staticmethod
    def _merge_todo(
        current: list[dict[str, str]],
        event: PlanEvent,
    ) -> list[dict[str, str]]:
        if not current:
            return [{"content": event.step, "status": event.status}]

        merged = [dict(item) for item in current]
        for item in merged:
            if item.get("content", "").strip() == event.step:
                item["status"] = event.status
                return merged

        while len(merged) < event.index:
            merged.append({"content": f"шаг {len(merged) + 1}", "status": "pending"})
        if event.index <= len(merged):
            merged[event.index - 1] = {"content": event.step, "status": event.status}
        else:
            merged.append({"content": event.step, "status": event.status})
        return merged
