"""Context Engineering: middleware и инструменты оркестратора."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from deepagents import HarnessProfile, register_harness_profile
from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.summarization import (
    SummarizationMiddleware,
    SummarizationToolMiddleware,
)
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ExtendedModelResponse,
    ModelRequest,
    ModelResponse,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, StructuredTool

from mentor.config import AppConfig
from mentor.events import CompactionEvent, FileOffloadEvent, SummarizationEvent

if TYPE_CHECKING:
    from mentor.agent import AgentRunContext

_ce_profile_registered = False


def ensure_ce_harness_profile() -> None:
    """Исключить дефолтный SummarizationMiddleware — подставим свой с порогами из конфига."""
    global _ce_profile_registered  # noqa: PLW0603
    if _ce_profile_registered:
        return
    register_harness_profile(
        "openrouter",
        HarnessProfile(
            excluded_middleware=frozenset({"SummarizationMiddleware"}),
        ),
    )
    _ce_profile_registered = True


SummarizationCallback = Callable[[dict[str, Any]], None]


def summarization_signature(raw_event: object) -> str | None:
    """Ключ дедупликации CE-события суммаризации."""
    if not isinstance(raw_event, dict):
        return None
    cutoff = raw_event.get("cutoff_index")
    file_path = raw_event.get("file_path")
    if cutoff is None:
        return None
    return f"{cutoff}:{file_path}"


def estimate_tokens_after_summarization(
    raw_event: dict[str, Any],
    summarization_threshold: int,
) -> int:
    """Оценка effective window после суммаризации (API input_tokens может не падать)."""
    keep_floor = ce_keep_tokens(summarization_threshold)
    summary_msg = raw_event.get("summary_message")
    summary_tokens = 0
    if summary_msg is not None:
        content = getattr(summary_msg, "content", "")
        if isinstance(content, str):
            summary_tokens = estimate_text_tokens(content)
        else:
            summary_tokens = estimate_text_tokens(str(content))
    return max(keep_floor, summary_tokens + 200)


COMPACTION_OVERFLOW_RATIO = 0.85


def compaction_overflow_threshold(context_limit: int) -> int:
    """Порог, после которого суммаризация классифицируется как компактизация."""
    return int(context_limit * COMPACTION_OVERFLOW_RATIO)


def format_compaction_overflow_trigger(context_limit: int) -> str:
    """Текст триггера для CE-панели компактизации (85% context_limit)."""
    threshold = compaction_overflow_threshold(context_limit)
    return f"окно достигло ≥85% context_limit ({threshold:,} / {context_limit:,} токенов)"


def build_summarization_ce_event(
    raw_event: dict[str, Any],
    *,
    tokens_before: int,
    config: AppConfig,
) -> SummarizationEvent | CompactionEvent:
    """Построить CE-событие из `_summarization_event` deepagents."""
    tokens_after = estimate_tokens_after_summarization(raw_event, config.summarization_threshold)
    if tokens_after >= tokens_before:
        tokens_after = max(1, tokens_before // 4)

    history_file = raw_event.get("file_path")
    if not isinstance(history_file, str):
        history_file = None

    overflow = tokens_before >= compaction_overflow_threshold(config.context_limit)
    if overflow:
        return CompactionEvent(
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            trigger=format_compaction_overflow_trigger(config.context_limit),
            context_limit=config.context_limit,
            history_file=history_file,
            dedupe_key=summarization_signature(raw_event) or "",
        )

    trigger_percent = int(tokens_before / config.context_limit * 100) if config.context_limit else 0
    dedupe_key = summarization_signature(raw_event) or ""
    return SummarizationEvent(
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        trigger_percent=trigger_percent,
        context_limit=config.context_limit,
        history_file=history_file,
        dedupe_key=dedupe_key,
    )


class _ReportingSummarizationMiddleware(AgentMiddleware):
    """Обёртка: `_summarization_event` — private state и не попадает в stream updates."""

    def __init__(
        self,
        inner: SummarizationMiddleware,
        *,
        on_summarization: SummarizationCallback,
    ) -> None:
        self._inner = inner
        self._on_summarization = on_summarization

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)

    @staticmethod
    def _extract_raw_event(
        response: ModelResponse | ExtendedModelResponse,
    ) -> dict[str, Any] | None:
        if not isinstance(response, ExtendedModelResponse):
            return None
        command = response.command
        if command is None:
            return None
        update = getattr(command, "update", None)
        if not isinstance(update, dict):
            return None
        raw = update.get("_summarization_event")
        return raw if isinstance(raw, dict) else None

    def _report(self, response: ModelResponse | ExtendedModelResponse) -> None:
        raw_event = self._extract_raw_event(response)
        if raw_event is not None:
            self._on_summarization(raw_event)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse | ExtendedModelResponse:
        response = self._inner.wrap_model_call(request, handler)
        self._report(response)
        return response

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse | ExtendedModelResponse:
        response = await self._inner.awrap_model_call(request, handler)
        self._report(response)
        return response


def ce_keep_tokens(summarization_threshold: int) -> int:
    """Сколько токенов оставить после суммаризации.

    Должно быть **меньше** порога trigger: иначе `_determine_cutoff_index`
    возвращает 0 (особенно при keep=fraction от max_input_tokens модели ~1M).
    """
    threshold = max(1, summarization_threshold)
    return max(400, min(threshold // 4, 8_000))


def build_ce_middleware(
    model: BaseChatModel,
    backend: BackendProtocol | Callable[..., BackendProtocol],
    config: AppConfig,
    *,
    on_summarization: SummarizationCallback | None = None,
) -> list[AgentMiddleware[Any, Any, Any]]:
    """Суммаризация по порогу + on-demand `compact_conversation`."""
    inner = SummarizationMiddleware(
        model=model,
        backend=backend,
        trigger=("tokens", config.summarization_threshold),
        keep=("tokens", ce_keep_tokens(config.summarization_threshold)),
    )
    summarization: SummarizationMiddleware | _ReportingSummarizationMiddleware = inner
    if on_summarization is not None:
        summarization = _ReportingSummarizationMiddleware(inner, on_summarization=on_summarization)
    return [
        summarization,
        SummarizationToolMiddleware(inner),
    ]


def estimate_text_tokens(text: str) -> int:
    """Грубая оценка токенов для CE-панелей (≈4 символа на токен)."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // 4)


def make_write_to_workspace_tool(ctx: AgentRunContext) -> BaseTool:
    """CE-tool: полный контент в файл, агенту — только summary + путь."""

    def _write_to_workspace(content: str, filename: str, summary: str) -> str:
        clean_name = filename.replace("\\", "/").lstrip("./")
        if clean_name.startswith("/"):
            clean_name = clean_name.removeprefix("/")
        target = ctx.workspace / clean_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        tokens_before = estimate_text_tokens(content)
        tokens_after = estimate_text_tokens(f"{clean_name}: {summary}")
        if ctx.on_event is not None:
            ctx.on_event(
                FileOffloadEvent(
                    filename=clean_name,
                    tokens_before=tokens_before,
                    tokens_after=tokens_after,
                ),
            )
        return (
            f"Сохранено в `{clean_name}`. "
            f"Кратко: {summary.strip()} "
            f"(полный текст — read_file `{clean_name}` при необходимости)."
        )

    return StructuredTool.from_function(
        func=_write_to_workspace,
        name="write_to_workspace",
        description=(
            "Context Engineering: записать объёмные данные в workspace и вернуть только "
            "краткое summary. Используй для длинных выдержек, агрегированных review-нот "
            "и больших списков — не держи их в сообщениях."
        ),
    )
