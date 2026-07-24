"""Трекинг контекста и файловых операций при стриминге агента."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import LLMResult
from langgraph.types import Command

from mentor.ce import (
    build_summarization_ce_event,
    estimate_tokens_after_summarization,
    summarization_signature,
)
from mentor.config import SPRINT03_BASELINE_DELTA, AppConfig
from mentor.events import (
    AgentEvent,
    CompactionEvent,
    ContextEvent,
    FileEvent,
    PlanEvent,
    SubagentEndEvent,
    UserQuestionEvent,
)

if TYPE_CHECKING:
    from mentor.agent import AgentRunContext

logger = logging.getLogger(__name__)

FILE_TOOLS = frozenset({"read_file", "grep", "glob", "ls"})
SERVICE_PATHS = frozenset(
    {
        "submission.md",
        "rubric.md",
        "code-index.md",
        "plan.md",
        "feedback.md",
        "fix_plan.md",
    }
)
SERVICE_PREFIXES = ("notes/", "briefs/")


def _usage_value(usage: object, key: str) -> int | None:
    if isinstance(usage, dict):
        value = usage.get(key)
        return value if isinstance(value, int) else None
    value = getattr(usage, key, None)
    return value if isinstance(value, int) else None


def extract_tokens_from_message(message: BaseMessage) -> int | None:
    """Извлечь input_tokens из AIMessage.usage_metadata."""
    usage = getattr(message, "usage_metadata", None)
    if usage is None:
        return None
    for key in ("input_tokens", "prompt_tokens", "total_tokens"):
        value = _usage_value(usage, key)
        if value is not None:
            return value
    return None


def extract_input_tokens(llm_result: LLMResult) -> int | None:
    """Извлечь input_tokens из ответа LLM."""
    llm_output = llm_result.llm_output
    if isinstance(llm_output, dict):
        token_usage = llm_output.get("token_usage")
        if isinstance(token_usage, dict):
            for key in ("input_tokens", "prompt_tokens"):
                value = token_usage.get(key)
                if isinstance(value, int):
                    return value

    for generation_list in llm_result.generations:
        for generation in generation_list:
            message = getattr(generation, "message", None)
            if isinstance(message, BaseMessage):
                tokens = extract_tokens_from_message(message)
                if tokens is not None:
                    return tokens
    return None


def extract_file_paths(tool_name: str, tool_input: Any) -> list[str]:
    """Извлечь пути файлов из аргументов файлового инструмента."""
    if tool_name not in FILE_TOOLS or not isinstance(tool_input, dict):
        return []

    paths: list[str] = []
    if tool_name == "glob":
        raw = tool_input.get("pattern")
        if isinstance(raw, str) and raw.strip():
            paths.append(raw.strip())

    for key in ("file_path", "path", "target_file"):
        raw = tool_input.get(key)
        if isinstance(raw, str) and raw.strip():
            paths.append(raw.strip())

    if tool_name == "grep":
        include = tool_input.get("include")
        if isinstance(include, str) and include.strip():
            paths.append(include.strip())

    return paths


def is_outside_student_code(path: str) -> bool:
    """Путь вне code/ и не служебный артефакт workspace."""
    normalized = path.replace("\\", "/").lstrip("./")
    if normalized.startswith("/"):
        normalized = normalized.removeprefix("/")
    if normalized.startswith("code/"):
        return False
    if normalized in SERVICE_PATHS:
        return False
    return not normalized.startswith(SERVICE_PREFIXES)


def format_files_preview(files: list[str], *, limit: int = 3) -> str:
    """Сжатое представление списка прочитанных файлов."""
    if not files:
        return ""
    unique = list(dict.fromkeys(files))
    head = ", ".join(unique[:limit])
    if len(unique) > limit:
        return f"{head} ... (+{len(unique) - limit} файл)"
    return head


def extract_file_events_from_message(message: BaseMessage) -> list[FileEvent]:
    """Извлечь FileEvent из tool_calls AIMessage."""
    if not isinstance(message, AIMessage):
        return []

    events: list[FileEvent] = []
    tool_calls = getattr(message, "tool_calls", None) or []
    for tool_call in tool_calls:
        if not isinstance(tool_call, dict):
            continue
        name = str(tool_call.get("name", ""))
        args = tool_call.get("args", {})
        events.extend(
            FileEvent(path=path, tool_name=name) for path in extract_file_paths(name, args)
        )
    return events


def _extract_messages(update: dict[str, Any]) -> list[BaseMessage]:
    raw_messages = update.get("messages")
    if not isinstance(raw_messages, list):
        return []
    return [msg for msg in raw_messages if isinstance(msg, BaseMessage)]


@dataclass
class _PendingCE:
    kind: str
    tokens_before: int
    trigger: str
    history_file: str | None = None


@dataclass
class _StreamTrackerState:
    todos_state: list[dict[str, str]] = field(default_factory=list)
    files_in_step: list[str] = field(default_factory=list)
    last_plan_keys: set[str] = field(default_factory=set)
    tokens_after: int = 0
    pending_ce: _PendingCE | None = None
    last_summarization_signature: str | None = None


def _emit_subagent_end_if_pending(
    *,
    emit: Callable[[AgentEvent], None],
    run_context: AgentRunContext | None,
    orchestrator_after: int,
    step: str,
) -> None:
    if run_context is None or run_context.pending_subagent is None:
        return
    if run_context.pending_subagent_result is None:
        return

    note_path, subagent_tokens = run_context.pending_subagent_result
    start = run_context.pending_subagent
    end_event = SubagentEndEvent(
        aspect=start.aspect,
        note_path=note_path,
        subagent_context_tokens=subagent_tokens,
        orchestrator_tokens_before=run_context.spawn_orchestrator_tokens_before,
        orchestrator_tokens_after=orchestrator_after,
        sprint03_baseline_delta=SPRINT03_BASELINE_DELTA,
    )
    emit(end_event)

    savings = end_event.savings
    run_context.subagent_savings_total += savings
    run_context.context_rows_meta.append(
        {
            "step": step or start.aspect,
            "method": "субагент",
            "delta": end_event.orchestrator_delta,
            "savings": savings,
        },
    )
    run_context.pending_subagent = None
    run_context.pending_subagent_result = None


def _collect_summarization_raw_events(update: dict[str, Any]) -> list[dict[str, Any]]:
    """Fallback: найти `_summarization_event` в update-chunk."""
    found: list[dict[str, Any]] = []

    def walk(payload: object) -> None:
        if not isinstance(payload, dict):
            return
        raw = payload.get("_summarization_event")
        if isinstance(raw, dict):
            found.append(raw)
        for value in payload.values():
            if isinstance(value, dict):
                walk(value)

    walk(update)
    return found


def _config_limits(run_context: AgentRunContext | None) -> tuple[int, int]:
    if run_context is None:
        return 128_000, 80_000
    return run_context.config.context_limit, run_context.config.summarization_threshold


def _summarization_signature(raw_event: object) -> str | None:
    return summarization_signature(raw_event)


def _estimate_tokens_after_summarization(
    raw_event: dict[str, Any],
    summarization_threshold: int,
) -> int:
    return estimate_tokens_after_summarization(raw_event, summarization_threshold)


def _emit_ce_from_summarization_event(
    raw_event: dict[str, Any],
    *,
    emit: Callable[[AgentEvent], None],
    state: _StreamTrackerState,
    run_context: AgentRunContext | None,
) -> None:
    """Fallback: если `_summarization_event` всё же попал в stream update."""
    signature = _summarization_signature(raw_event)
    if signature is None or signature == state.last_summarization_signature:
        return
    state.last_summarization_signature = signature

    context_limit, summarization_threshold = _config_limits(run_context)
    tokens_before = state.tokens_after
    if run_context is not None:
        event = build_summarization_ce_event(
            raw_event,
            tokens_before=tokens_before,
            config=run_context.config,
        )
    else:
        event = build_summarization_ce_event(
            raw_event,
            tokens_before=tokens_before,
            config=AppConfig(
                openrouter_api_key="test",
                context_limit=context_limit,
                summarization_threshold=summarization_threshold,
            ),
        )
    emit(event)


def _emit_ce_from_compact_tool(
    *,
    emit: Callable[[AgentEvent], None],
    state: _StreamTrackerState,
    run_context: AgentRunContext | None,
    tool_call_id: str,
) -> None:
    """CE-панель для ручного `compact_conversation` (private state не в stream)."""
    signature = f"compact:{tool_call_id}"
    if signature == state.last_summarization_signature:
        return
    state.last_summarization_signature = signature

    context_limit, _ = _config_limits(run_context)
    tokens_before = state.tokens_after
    tokens_after = max(1, tokens_before // 4)
    emit(
        CompactionEvent(
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            trigger="compact_conversation",
            context_limit=context_limit,
            dedupe_key=signature,
        ),
    )


def _emit_pending_ce_if_applicable(
    *,
    emit: Callable[[AgentEvent], None],
    state: _StreamTrackerState,
    tokens_after: int,
    run_context: AgentRunContext | None,
) -> None:
    """Эмитить CE после `compact_conversation`, когда API сообщает падение input_tokens."""
    pending = state.pending_ce
    if pending is None or pending.kind != "compaction" or tokens_after >= pending.tokens_before:
        return

    context_limit, _ = _config_limits(run_context)
    emit(
        CompactionEvent(
            tokens_before=pending.tokens_before,
            tokens_after=tokens_after,
            trigger=pending.trigger,
            context_limit=context_limit,
            history_file=pending.history_file,
        ),
    )
    state.pending_ce = None


def _detect_compaction_tool(message: BaseMessage) -> bool:
    if not isinstance(message, AIMessage):
        return False
    tool_calls = getattr(message, "tool_calls", None) or []
    return any(
        isinstance(tool_call, dict) and str(tool_call.get("name", "")) == "compact_conversation"
        for tool_call in tool_calls
    )


TodosCallback = Callable[[list[dict[str, str]]], None]


def _process_stream_update(
    update: dict[str, Any],
    *,
    emit: Callable[[AgentEvent], None],
    state: _StreamTrackerState,
    run_context: AgentRunContext | None = None,
    on_todos_update: TodosCallback | None = None,
) -> None:
    """Обработать один update-chunk: todos, messages, контекст, CE."""
    # Суммаризация эмитится из middleware-callback; stream дублирует private state.
    if run_context is None:
        for raw_event in _collect_summarization_raw_events(update):
            _emit_ce_from_summarization_event(
                raw_event,
                emit=emit,
                state=state,
                run_context=run_context,
            )

    todos = _extract_todos(update)
    if todos is not None:
        state.todos_state.clear()
        state.todos_state.extend(todos)
        if on_todos_update is not None:
            on_todos_update(todos)
        total = len(todos)
        for index, todo in enumerate(todos, start=1):
            content = todo.get("content", "").strip()
            status = todo.get("status", "pending")
            key = f"{content}|{status}"
            if key in state.last_plan_keys:
                continue
            state.last_plan_keys.add(key)
            emit(
                PlanEvent(
                    step=content,
                    status=status,
                    index=index,
                    total=total,
                ),
            )

    for message in _extract_messages(update):
        for file_event in extract_file_events_from_message(message):
            emit(file_event)

        if isinstance(message, ToolMessage):
            tool_name = str(getattr(message, "name", ""))
            if tool_name == "compact_conversation" and "Conversation compacted" in str(
                message.content
            ):
                _emit_ce_from_compact_tool(
                    emit=emit,
                    state=state,
                    run_context=run_context,
                    tool_call_id=str(getattr(message, "tool_call_id", "")),
                )
            if tool_name in FILE_TOOLS:
                logger.debug(
                    "tool message",
                    extra={"tool": tool_name, "content_len": len(str(message.content))},
                )

        if not isinstance(message, AIMessage):
            continue

        if _detect_compaction_tool(message):
            state.pending_ce = _PendingCE(
                kind="compaction",
                tokens_before=state.tokens_after,
                trigger="compact_conversation",
            )

        input_tokens = extract_tokens_from_message(message)
        if input_tokens is None:
            logger.debug("ai message without usage metadata")
            continue

        prev_tokens = state.tokens_after
        if input_tokens >= prev_tokens:
            tokens_before = prev_tokens
            tokens_after = input_tokens
        else:
            tokens_before = 0
            tokens_after = input_tokens
        state.tokens_after = tokens_after

        step = _current_step_from_todos(state.todos_state)
        method = "прямой"
        sprint03_baseline_delta = None
        savings = None
        if run_context is not None and run_context.pending_subagent_result is not None:
            method = "субагент"
            sprint03_baseline_delta = SPRINT03_BASELINE_DELTA
            savings = SPRINT03_BASELINE_DELTA - (tokens_after - run_context.orchestrator_tokens)

        if run_context is not None:
            run_context.orchestrator_tokens = tokens_after

        _emit_subagent_end_if_pending(
            emit=emit,
            run_context=run_context,
            orchestrator_after=tokens_after,
            step=step,
        )

        event = ContextEvent(
            step=step,
            tokens_before=tokens_before,
            tokens_after=state.tokens_after,
            files_read=list(state.files_in_step),
            method=method,
            sprint03_baseline_delta=sprint03_baseline_delta,
            savings=savings,
        )
        logger.debug(
            "context event",
            extra={
                "step": event.step,
                "tokens_before": event.tokens_before,
                "tokens_after": event.tokens_after,
                "delta": event.delta,
            },
        )
        emit(event)

        _emit_pending_ce_if_applicable(
            emit=emit,
            state=state,
            tokens_after=state.tokens_after,
            run_context=run_context,
        )

        state.files_in_step.clear()


def _extract_todos(update: dict[str, Any]) -> list[dict[str, str]] | None:
    todos = update.get("todos")
    if not isinstance(todos, list):
        return None
    return [
        {
            "content": str(item.get("content", "")),
            "status": str(item.get("status", "pending")),
        }
        for item in todos
        if isinstance(item, dict)
    ]


def _current_step_from_todos(todos: list[dict[str, str]]) -> str:
    for todo in todos:
        if todo.get("status") == "in_progress":
            return str(todo.get("content", "")).strip() or "шаг агента"
    for todo in reversed(todos):
        if todo.get("status") == "completed":
            return str(todo.get("content", "")).strip() or "шаг агента"
    if todos:
        return str(todos[0].get("content", "")).strip() or "шаг агента"
    return "шаг агента"


def _extract_interrupt_question(interrupt_value: object) -> str:
    if isinstance(interrupt_value, dict):
        for key in ("question", "value", "message"):
            raw = interrupt_value.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        action_requests = interrupt_value.get("action_requests")
        if isinstance(action_requests, list):
            for action in action_requests:
                if not isinstance(action, dict):
                    continue
                args = action.get("arguments") or action.get("args")
                if isinstance(args, dict):
                    question = args.get("question")
                    if isinstance(question, str) and question.strip():
                        return question.strip()
                description = action.get("description")
                if isinstance(description, str) and description.strip():
                    return description.strip()
    if interrupt_value is not None:
        return str(interrupt_value).strip()
    return "Уточните тип проекта (FastAPI-сервис, CLI-утилита или другое):"


def _resolve_interrupt_answer(
    interrupt_value: object,
    run_context: AgentRunContext | None,
) -> str:
    question = _extract_interrupt_question(interrupt_value)
    if run_context is not None and run_context.user_answer_callback is not None:
        if run_context.on_event is not None:
            run_context.on_event(UserQuestionEvent(question=question))
        return run_context.user_answer_callback(question)
    if run_context is not None and run_context.pending_user_answer is not None:
        return run_context.pending_user_answer
    return question


def stream_with_tracking(
    agent: Any,
    input_state: dict[str, Any] | Command[Any],
    run_config: dict[str, Any],
    *,
    on_event: Callable[[AgentEvent], None] | None = None,
    on_todos_update: TodosCallback | None = None,
    initial_tokens: int = 0,
    run_context: AgentRunContext | None = None,
) -> int:
    """Стримить агента и эмитить события мониторинга.

    Returns:
        Размер контекста после завершения стрима (для carry-over между retry).

    """
    state = _StreamTrackerState(tokens_after=initial_tokens)
    if run_context is not None:
        run_context.orchestrator_tokens = initial_tokens

    def emit(event: AgentEvent) -> None:
        if isinstance(event, FileEvent):
            state.files_in_step.append(event.path)
        if on_event is not None:
            on_event(event)

    stream_input: dict[str, Any] | Command[Any] = input_state
    while True:
        interrupted = False
        interrupt_value: object = None

        stream = agent.stream(
            stream_input,
            config=run_config,
            stream_mode="updates",
        )
        for chunk in stream:
            if isinstance(chunk, dict) and "__interrupt__" in chunk:
                interrupted = True
                raw_interrupts = chunk["__interrupt__"]
                if raw_interrupts:
                    interrupt_value = raw_interrupts[0].value
                continue
            if not isinstance(chunk, dict):
                continue
            for update in chunk.values():
                if not isinstance(update, dict):
                    continue
                _process_stream_update(
                    update,
                    emit=emit,
                    state=state,
                    run_context=run_context,
                    on_todos_update=on_todos_update,
                )

        if not interrupted:
            break

        answer = _resolve_interrupt_answer(interrupt_value, run_context)
        if run_context is not None:
            run_context.pending_user_answer = answer
        stream_input = Command(resume={"decisions": [{"type": "approve"}]})

    return state.tokens_after
