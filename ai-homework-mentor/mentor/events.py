"""Структурированные события мониторинга агента."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlanEvent:
    """Обновление шага плана (todo)."""

    step: str
    status: str
    index: int
    total: int


@dataclass(frozen=True)
class FileEvent:
    """Чтение файла через файловый инструмент."""

    path: str
    tool_name: str


@dataclass(frozen=True)
class ContextEvent:
    """Изменение размера контекста после шага LLM."""

    step: str
    tokens_before: int
    tokens_after: int
    files_read: list[str] = field(default_factory=list)
    method: str = "прямой"
    sprint03_baseline_delta: int | None = None
    savings: int | None = None

    @property
    def delta(self) -> int:
        """Прирост токенов на шаге."""
        return self.tokens_after - self.tokens_before


@dataclass(frozen=True)
class SubagentStartEvent:
    """Запуск изолированного Reviewer-субагента."""

    aspect: str
    brief_path: str
    brief_tokens: int
    files_preview: str = ""


@dataclass(frozen=True)
class SubagentEndEvent:
    """Завершение Reviewer-субагента."""

    aspect: str
    note_path: str
    subagent_context_tokens: int
    orchestrator_tokens_before: int
    orchestrator_tokens_after: int
    sprint03_baseline_delta: int = 4500

    @property
    def orchestrator_delta(self) -> int:
        """Прирост контекста оркестратора после делегирования."""
        return self.orchestrator_tokens_after - self.orchestrator_tokens_before

    @property
    def savings(self) -> int:
        """Экономия относительно прямой проверки в Sprint 03."""
        return self.sprint03_baseline_delta - self.orchestrator_delta


@dataclass(frozen=True)
class FileOffloadEvent:
    """Явный вынос объёмных данных в файл (write_to_workspace)."""

    filename: str
    tokens_before: int
    tokens_after: int

    @property
    def savings(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)


@dataclass(frozen=True)
class SummarizationEvent:
    """Автоматическая суммаризация истории (SummarizationMiddleware)."""

    tokens_before: int
    tokens_after: int
    trigger_percent: int
    context_limit: int
    history_file: str | None = None
    dedupe_key: str = ""

    @property
    def savings(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)


@dataclass(frozen=True)
class CompactionEvent:
    """Компактизация: compact_conversation или overflow near context_limit."""

    tokens_before: int
    tokens_after: int
    trigger: str
    context_limit: int
    history_file: str | None = None
    dedupe_key: str = ""

    @property
    def savings(self) -> int:
        return max(0, self.tokens_before - self.tokens_after)


@dataclass(frozen=True)
class SkillEvent:
    """Подключение навыка к аспекту рубрики."""

    aspect: str
    skill_name: str | None
    skill_found: bool


@dataclass(frozen=True)
class TopicDetectedEvent:
    """Тема определена автоматически или указана явно."""

    topic: str
    source: str  # "cli" | "auto" | "user"


@dataclass(frozen=True)
class RubricSelectedEvent:
    """Выбранная рубрика проверки."""

    rubric_file: str
    aspect_count: int
    topic: str


@dataclass(frozen=True)
class UserQuestionEvent:
    """Уточняющий вопрос пользователю (human-in-the-loop)."""

    question: str


AgentEvent = (
    PlanEvent
    | FileEvent
    | ContextEvent
    | SubagentStartEvent
    | SubagentEndEvent
    | FileOffloadEvent
    | SummarizationEvent
    | CompactionEvent
    | SkillEvent
    | TopicDetectedEvent
    | RubricSelectedEvent
    | UserQuestionEvent
)
