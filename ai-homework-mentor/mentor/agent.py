"""Orchestrator-агент на deepagents."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.messages import HumanMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.types import interrupt

from mentor.brief import (
    BriefError,
    build_all_briefs,
    estimate_tokens,
    load_rubric_aspects,
    parse_aspect_from_brief_path,
    resolve_aspect_id,
)
from mentor.ce import (
    build_ce_middleware,
    build_summarization_ce_event,
    ensure_ce_harness_profile,
    make_write_to_workspace_tool,
    summarization_signature,
)
from mentor.config import CONFIG_DIR, AppConfig
from mentor.events import (
    AgentEvent,
    RubricSelectedEvent,
    SkillEvent,
    SubagentStartEvent,
    TopicDetectedEvent,
    UserQuestionEvent,
)
from mentor.openrouter import build_chat_model
from mentor.parser import Submission, write_submission_md
from mentor.prompts import PromptLoadError, load_yaml_prompt
from mentor.render import read_code_index_stats
from mentor.reviewer import ReviewerError, run_reviewer
from mentor.rubric import (
    RubricError,
    detect_topic,
    normalize_topic_label,
    prepare_rubric,
    read_code_index,
)
from mentor.tracker import stream_with_tracking

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[list[dict[str, str]]], None]
RetryCallback = Callable[[int, int], None]
AgentEventCallback = Callable[[AgentEvent], None]
UserAnswerCallback = Callable[[str], str]

REQUIRED_ARTIFACTS = ("plan.md", "feedback.md", "fix_plan.md")


class OrchestratorError(Exception):
    """Ошибка выполнения orchestrator-агента."""


@dataclass
class AgentRunContext:
    """Общий контекст запуска оркестратора для tool callbacks и трекера."""

    workspace: Path
    config: AppConfig
    submission: Submission
    orchestrator_tokens: int = 0
    on_event: AgentEventCallback | None = None
    pending_subagent: SubagentStartEvent | None = None
    pending_subagent_result: tuple[str, int] | None = None
    spawn_orchestrator_tokens_before: int = 0
    subagent_savings_total: int = 0
    context_rows_meta: list[dict[str, str | int]] = field(default_factory=list)
    last_summarization_signature: str | None = None
    resolved_topic: str | None = None
    rubric_file: str | None = None
    topic_source: str = "cli"
    pending_user_answer: str | None = None
    user_answer_callback: UserAnswerCallback | None = None
    topic_needs_clarification: bool = False
    auto_topic: str | None = None
    ask_user_consumed: bool = False
    plan_needs_rebuild: bool = False


def _emit(event: AgentEventCallback | None, payload: AgentEvent) -> None:
    if event is not None:
        event(payload)


def _reset_workspace_after_topic_change(workspace: Path) -> None:
    """Удалить артефакты плана от предыдущей рубрики (до HITL)."""
    plan_path = workspace / "plan.md"
    if plan_path.exists():
        plan_path.unlink()
    notes_dir = workspace / "notes"
    if notes_dir.is_dir():
        for note in notes_dir.glob("review-*.md"):
            note.unlink()


def _apply_topic_answer(ctx: AgentRunContext, answer: str) -> str:
    """Обновить рубрику и submission после ответа пользователя."""
    ctx.resolved_topic = answer
    ctx.topic_source = "user"
    ctx.auto_topic = None
    ctx.topic_needs_clarification = False
    ctx.plan_needs_rebuild = True

    _reset_workspace_after_topic_change(ctx.workspace)
    _emit(
        ctx.on_event,
        TopicDetectedEvent(topic=answer, source="user"),
    )

    normalized = normalize_topic_label(answer)
    _, rubric_file, display_topic = prepare_rubric(ctx.workspace, normalized)
    ctx.rubric_file = rubric_file
    brief_paths = build_all_briefs(
        ctx.workspace,
        topic=display_topic,
        on_skill=lambda aspect, skill_name, skill_found: _emit(
            ctx.on_event,
            SkillEvent(aspect=aspect, skill_name=skill_name, skill_found=skill_found),
        ),
    )
    _emit(
        ctx.on_event,
        RubricSelectedEvent(
            rubric_file=rubric_file,
            aspect_count=len(brief_paths),
            topic=display_topic,
        ),
    )
    updated = Submission(
        source_type=ctx.submission.source_type,
        source=ctx.submission.source,
        topic=answer,
    )
    ctx.submission = updated
    write_submission_md(ctx.workspace, updated)
    return answer


def _ask_user_impl(question: str, ctx: AgentRunContext) -> str:
    if ctx.auto_topic is not None:
        label = "FastAPI" if ctx.auto_topic == "fastapi" else "Python CLI"
        return (
            f"Тема уже определена автоматически ({label}). "
            "ask_user не нужен — продолжай проверку по rubric.md."
        )
    if ctx.ask_user_consumed:
        return "ask_user уже вызывался в этой сессии. Продолжай проверку по rubric.md."

    if ctx.pending_user_answer is not None:
        answer = ctx.pending_user_answer.strip()
        ctx.pending_user_answer = None
        ctx.ask_user_consumed = True
        return _apply_topic_answer(ctx, answer)

    ctx.ask_user_consumed = True
    if ctx.user_answer_callback is not None:
        if ctx.on_event is not None:
            _emit(ctx.on_event, UserQuestionEvent(question=question))
        answer = ctx.user_answer_callback(question).strip()
    else:
        _emit(ctx.on_event, UserQuestionEvent(question=question))
        raw = interrupt({"type": "user_question", "question": question})
        answer = str(raw).strip()

    return _apply_topic_answer(ctx, answer)


def setup_rubric_and_briefs(
    submission: Submission,
    workspace: Path,
    *,
    on_event: AgentEventCallback | None = None,
) -> tuple[str, str, int, str | None]:
    """Выбрать рубрику, записать briefs; вернуть (topic, rubric_file, count, auto_topic)."""
    code_index = read_code_index(workspace)
    code_dir = workspace / "code"
    explicit_topic = submission.topic
    auto_topic = (
        detect_topic(submission, code_index, code_dir=code_dir) if explicit_topic is None else None
    )

    if explicit_topic is not None:
        topic_key = normalize_topic_label(explicit_topic) or explicit_topic
        source = "cli"
        _emit(on_event, TopicDetectedEvent(topic=explicit_topic, source=source))
    elif auto_topic is not None:
        topic_key = auto_topic
        source = "auto"
        display = "FastAPI" if auto_topic == "fastapi" else "Python CLI"
        _emit(on_event, TopicDetectedEvent(topic=display, source=source))
    else:
        topic_key = None

    _, rubric_file, display_topic = prepare_rubric(workspace, topic_key)
    aspects = build_all_briefs(
        workspace,
        topic=display_topic,
        on_skill=lambda aspect, skill_name, skill_found: _emit(
            on_event,
            SkillEvent(aspect=aspect, skill_name=skill_name, skill_found=skill_found),
        ),
    )
    _emit(
        on_event,
        RubricSelectedEvent(
            rubric_file=rubric_file,
            aspect_count=len(aspects),
            topic=display_topic,
        ),
    )
    return display_topic, rubric_file, len(aspects), auto_topic


def build_user_message(
    submission: Submission,
    *,
    topic_needs_clarification: bool = False,
    auto_topic: str | None = None,
) -> str:
    """Сформировать стартовое сообщение для агента."""
    topic = submission.topic or "не указана"
    clarify_hint = ""
    if auto_topic is not None:
        label = "FastAPI" if auto_topic == "fastapi" else "Python CLI"
        clarify_hint = (
            f"\nТема определена автоматически: {label}. "
            "ask_user запрещён — используй rubric.md и briefs/ как есть.\n"
        )
    elif topic_needs_clarification:
        clarify_hint = (
            "\nТема не определена автоматически. "
            "Вызови ask_user ровно один раз с уточняющим вопросом о типе проекта "
            "(FastAPI-сервис, CLI-утилита или другое), затем продолжай проверку.\n"
        )
    return (
        "Проверь домашнее задание студента.\n\n"
        f"Тема: {topic}\n"
        f"Источник: {submission.source} ({submission.source_type})\n"
        f"{clarify_hint}\n"
        "Артефакты уже в workspace: submission.md, code/, code-index.md, rubric.md.\n"
        "Брифы для аспектов уже подготовлены в briefs/ — не перезаписывай их без необходимости.\n"
        "Делегируй проверку каждого аспекта Reviewer-субагентам через spawn_reviewer.\n"
        "Выполни полную проверку по рубрике и создай все требуемые файлы.\n"
        "Начни с read_file и write_todos — не отвечай текстом без tool call."
    )


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


def _artifact_files(workspace: Path) -> frozenset[str]:
    return frozenset(
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    )


def _review_notes_count(workspace: Path) -> int:
    notes_dir = workspace / "notes"
    if not notes_dir.exists():
        return 0
    return len(list(notes_dir.glob("review-*.md")))


def _missing_artifacts(workspace: Path) -> list[str]:
    missing = [name for name in REQUIRED_ARTIFACTS if not (workspace / name).exists()]
    if _review_notes_count(workspace) == 0:
        missing.append("notes/review-*.md")
    return missing


def _next_orchestrator_action(workspace: Path) -> str:
    """Конкретная подсказка для retry — снижает «пустые» ответы модели."""
    rubric_path = workspace / "rubric.md"
    if rubric_path.exists():
        try:
            aspects = load_rubric_aspects(rubric_path)
        except BriefError:
            aspects = []
        for aspect in aspects:
            note_path = workspace / "notes" / f"review-{aspect.id}.md"
            if not note_path.exists():
                return (
                    f"Следующий шаг: вызови spawn_reviewer с "
                    f"briefs/brief-{aspect.id}.md для аспекта «{aspect.name}», "
                    f"затем read_file notes/review-{aspect.id}.md."
                )
    if not (workspace / "feedback.md").exists() or not (workspace / "fix_plan.md").exists():
        return (
            "Все ReviewNote готовы. Следующий шаг: read_file по notes/review-*.md, "
            "затем write_file feedback.md и fix_plan.md. spawn_reviewer запрещён."
        )
    return (
        "Следующий шаг — вызови инструмент (read_file, write_file, spawn_reviewer или write_todos)."
    )


def _plan_rebuild_hint(*, plan_needs_rebuild: bool) -> str:
    if not plan_needs_rebuild:
        return ""
    return (
        "Рубрика обновлена после ответа пользователя. Старый plan.md удалён.\n"
        "Перечитай rubric.md и создай новый plan.md и write_todos "
        "только по аспектам текущей рубрики.\n\n"
    )


def _build_continue_message(workspace: Path, *, plan_needs_rebuild: bool = False) -> str:
    missing = _missing_artifacts(workspace)
    created = sorted(_artifact_files(workspace))
    preview_limit = 12
    created_preview = ", ".join(created[:preview_limit])
    if len(created) > preview_limit:
        created_preview += ", ..."
    return (
        f"{_plan_rebuild_hint(plan_needs_rebuild=plan_needs_rebuild)}"
        "Продолжи проверку с того места, где остановился.\n\n"
        f"Ещё не создано: {', '.join(missing)}.\n"
        f"Уже есть в workspace: {created_preview or '(пусто)'}.\n\n"
        f"{_next_orchestrator_action(workspace)}\n"
        "Не отвечай текстом без tool call, пока не будут готовы feedback.md и fix_plan.md."
    )


def _build_retry_message(
    submission: Submission,
    workspace: Path,
    *,
    auto_topic: str | None = None,
    topic_needs_clarification: bool = False,
    plan_needs_rebuild: bool = False,
) -> str:
    """Полный перезапуск задачи, если предыдущая попытка не создала артефактов."""
    intro = build_user_message(
        submission,
        topic_needs_clarification=topic_needs_clarification,
        auto_topic=auto_topic,
    )
    return f"{intro}\n\n{_build_continue_message(workspace, plan_needs_rebuild=plan_needs_rebuild)}"


def _normalize_brief_path(brief_path: str, workspace: Path) -> Path:
    clean = brief_path.replace("\\", "/").strip()
    if clean.startswith("/"):
        clean = clean.removeprefix("/")
    candidate = Path(clean)
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(workspace)
        except ValueError as exc:
            msg = f"бриф вне workspace: {brief_path}"
            raise OrchestratorError(msg) from exc
    return candidate


def _spawn_reviewer_impl(brief_path: str, ctx: AgentRunContext) -> str:
    relative_brief = _normalize_brief_path(brief_path, ctx.workspace)
    absolute_brief = ctx.workspace / relative_brief
    if not absolute_brief.exists():
        return (
            f"бриф не найден: {relative_brief.as_posix()}. "
            "Сначала создай файл через write_file в briefs/, "
            "затем повтори spawn_reviewer."
        )

    try:
        raw_aspect = parse_aspect_from_brief_path(relative_brief)
        aspect = resolve_aspect_id(raw_aspect, ctx.workspace / "rubric.md")
    except BriefError as exc:
        brief_posix = relative_brief.as_posix()
        return f"ошибка брифа `{brief_posix}`: {exc}. Исправь файл и повтори spawn_reviewer."

    if raw_aspect != aspect:
        logger.warning(
            "brief aspect id normalized",
            extra={"raw": raw_aspect, "resolved": aspect, "brief": relative_brief.as_posix()},
        )

    brief_text = absolute_brief.read_text(encoding="utf-8")
    brief_tokens = estimate_tokens(brief_text)
    files_preview = ""
    for line in brief_text.splitlines():
        if line.strip().startswith("- `code/"):
            files_preview = line.strip().removeprefix("- ").strip("`")
            break

    start_event = SubagentStartEvent(
        aspect=aspect,
        brief_path=relative_brief.as_posix(),
        brief_tokens=brief_tokens,
        files_preview=files_preview,
    )
    ctx.pending_subagent = start_event
    if ctx.on_event is not None:
        ctx.on_event(start_event)

    orchestrator_before = ctx.orchestrator_tokens
    ctx.spawn_orchestrator_tokens_before = orchestrator_before
    try:
        result = run_reviewer(relative_brief, ctx.workspace, ctx.config)
    except ReviewerError as exc:
        ctx.pending_subagent = None
        ctx.pending_subagent_result = None
        logger.warning(
            "reviewer failed",
            extra={"aspect": aspect, "error": str(exc)},
        )
        return (
            f"ошибка reviewer `{aspect}`: {exc}. Повтори spawn_reviewer с briefs/brief-{aspect}.md."
        )

    note_relative = f"notes/review-{aspect}.md"
    ctx.pending_subagent_result = (note_relative, result.subagent_context_tokens)
    return (
        f"готово: {note_relative} "
        f"(aspect={aspect}, subagent_tokens={result.subagent_context_tokens}). "
        "Прочитай ReviewNote через read_file перед синтезом."
    )


def make_ask_user_tool(ctx: AgentRunContext) -> StructuredTool:
    """Создать tool ask_user для уточнения темы."""

    def _ask_user(question: str) -> str:
        return _ask_user_impl(question, ctx)

    return StructuredTool.from_function(
        func=_ask_user,
        name="ask_user",
        description=(
            "Задать пользователю один уточняющий вопрос о типе проекта. "
            "Используй только если тема не указана в CLI и не определена автоматически."
        ),
    )


def make_spawn_reviewer_tool(ctx: AgentRunContext) -> StructuredTool:
    """Создать tool spawn_reviewer с доступом к run context."""

    def _spawn_reviewer(brief_path: str) -> str:
        return _spawn_reviewer_impl(brief_path, ctx)

    return StructuredTool.from_function(
        func=_spawn_reviewer,
        name="spawn_reviewer",
        description=(
            "Запустить изолированного Reviewer-субагента для одного аспекта. "
            "Передай путь к брифу (например briefs/brief-structure.md). "
            "Субагент запишет notes/review-<aspect>.md и вернёт короткий статус."
        ),
    )


def _stream_agent(
    agent: Any,
    input_state: dict[str, Any],
    run_config: dict[str, Any],
    *,
    on_todos_update: ProgressCallback | None,
    on_agent_event: AgentEventCallback | None = None,
    initial_tokens: int = 0,
    run_context: AgentRunContext | None = None,
) -> int:
    if on_agent_event is not None or run_context is not None:
        return stream_with_tracking(
            agent,
            input_state,
            run_config,
            on_event=on_agent_event,
            on_todos_update=on_todos_update,
            initial_tokens=initial_tokens,
            run_context=run_context,
        )

    stream = agent.stream(
        input_state,
        config=run_config,
        stream_mode="updates",
    )
    for chunk in stream:
        if not isinstance(chunk, dict):
            continue
        for update in chunk.values():
            if not isinstance(update, dict):
                continue
            todos = _extract_todos(update)
            if todos and on_todos_update is not None:
                on_todos_update(todos)
    return initial_tokens


def _artifact_error_message(workspace: Path) -> str:
    missing = _missing_artifacts(workspace)
    notes_count = _review_notes_count(workspace)
    return (
        "агент не завершил проверку — не хватает артефактов: "
        f"{', '.join(missing)}. "
        f"Создано review-нот: {notes_count}. "
        "Модель иногда завершает цикл без tool call — запустите команду ещё раз "
        "или смените MODEL в .env."
    )


def _recursion_limit_error_message(workspace: Path, *, limit: int) -> str:
    file_count, line_count = read_code_index_stats(workspace)
    notes_count = _review_notes_count(workspace)
    size_hint = ""
    if file_count > 0:
        size_hint = f" Проект: ~{file_count} файлов, ~{line_count:,} строк."
    return (
        f"проверка не завершилась: исчерпан лимит шагов агента ({limit})."
        f"{size_hint} "
        f"Создано review-нот: {notes_count}. "
        "Попробуйте меньший репозиторий или увеличьте AGENT_RECURSION_LIMIT в .env."
    )


def _llm_timeout_error_message(config: AppConfig) -> str:
    return (
        f"проверка не завершилась: OpenRouter не ответил за {config.llm_request_timeout} с. "
        "Увеличьте LLM_REQUEST_TIMEOUT в .env или повторите команду."
    )


def run_orchestrator(
    submission: Submission,
    workspace: Path,
    config: AppConfig,
    *,
    on_todos_update: ProgressCallback | None = None,
    on_retry: RetryCallback | None = None,
    on_agent_event: AgentEventCallback | None = None,
    user_answer_callback: UserAnswerCallback | None = None,
) -> Path:
    """Запустить orchestrator-агент; вернуть path к feedback.md."""
    os.environ["OPENROUTER_API_KEY"] = config.openrouter_api_key

    prompt_path = CONFIG_DIR / "prompts" / "orchestrator-system.yaml"
    try:
        system_prompt = load_yaml_prompt(prompt_path)
    except PromptLoadError as exc:
        raise OrchestratorError(str(exc)) from exc

    (workspace / "briefs").mkdir(parents=True, exist_ok=True)
    (workspace / "notes").mkdir(parents=True, exist_ok=True)

    code_index = read_code_index(workspace)
    code_dir = workspace / "code"
    auto_topic = (
        detect_topic(submission, code_index, code_dir=code_dir)
        if submission.topic is None
        else None
    )
    topic_needs_clarification = submission.topic is None and auto_topic is None

    try:
        display_topic, rubric_file, _, setup_auto_topic = setup_rubric_and_briefs(
            submission,
            workspace,
            on_event=on_agent_event,
        )
    except RubricError as exc:
        raise OrchestratorError(str(exc)) from exc

    run_context = AgentRunContext(
        workspace=workspace,
        config=config,
        submission=submission,
        on_event=on_agent_event,
        user_answer_callback=user_answer_callback,
        topic_needs_clarification=topic_needs_clarification,
        rubric_file=rubric_file,
        resolved_topic=display_topic,
        auto_topic=setup_auto_topic,
    )

    def on_summarization(raw_event: dict[str, Any]) -> None:
        if on_agent_event is None:
            return
        signature = summarization_signature(raw_event)
        if signature is None or signature == run_context.last_summarization_signature:
            return
        tokens_before = run_context.orchestrator_tokens
        if tokens_before < config.summarization_threshold // 2:
            return
        run_context.last_summarization_signature = signature
        on_agent_event(
            build_summarization_ce_event(
                raw_event,
                tokens_before=tokens_before,
                config=config,
            ),
        )

    spawn_tool = make_spawn_reviewer_tool(run_context)
    write_tool = make_write_to_workspace_tool(run_context)
    ask_tool = make_ask_user_tool(run_context)

    ensure_ce_harness_profile()
    backend = FilesystemBackend(root_dir=workspace, virtual_mode=True)
    chat_model = build_chat_model(config)
    ce_middleware = build_ce_middleware(
        chat_model,
        backend,
        config,
        on_summarization=on_summarization,
    )

    agent = create_deep_agent(
        model=chat_model,
        backend=backend,
        system_prompt=system_prompt,
        tools=[spawn_tool, write_tool, ask_tool],
        middleware=ce_middleware,
        interrupt_on={"ask_user": True},
        checkpointer=MemorySaver(),
    )

    thread_id = uuid4().hex
    run_config: dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": config.agent_recursion_limit,
    }

    logger.info("orchestrator started", extra={"workspace": workspace.as_posix()})

    last_snapshot = _artifact_files(workspace)
    last_notes = _review_notes_count(workspace)
    session_tokens = 0

    try:
        for attempt in range(1, config.agent_max_attempts + 1):
            plan_rebuild = run_context.plan_needs_rebuild
            if attempt == 1:
                message = build_user_message(
                    run_context.submission,
                    topic_needs_clarification=run_context.topic_needs_clarification,
                    auto_topic=run_context.auto_topic,
                )
            elif (
                _artifact_files(workspace) == last_snapshot
                and _review_notes_count(workspace) == last_notes
                and _review_notes_count(workspace) == 0
            ):
                thread_id = uuid4().hex
                run_config["configurable"]["thread_id"] = thread_id
                run_context.last_summarization_signature = None
                message = _build_retry_message(
                    run_context.submission,
                    workspace,
                    auto_topic=run_context.auto_topic,
                    topic_needs_clarification=run_context.topic_needs_clarification,
                    plan_needs_rebuild=plan_rebuild,
                )
                logger.warning(
                    "orchestrator fresh retry",
                    extra={"attempt": attempt, "thread_id": thread_id},
                )
            else:
                message = _build_continue_message(
                    workspace,
                    plan_needs_rebuild=plan_rebuild,
                )

            if plan_rebuild:
                run_context.plan_needs_rebuild = False
                last_snapshot = _artifact_files(workspace)
                last_notes = _review_notes_count(workspace)

            if attempt > 1:
                logger.warning(
                    "orchestrator retry",
                    extra={"attempt": attempt, "missing": _missing_artifacts(workspace)},
                )
                if on_retry is not None:
                    on_retry(attempt, config.agent_max_attempts)

            try:
                session_tokens = stream_with_tracking(
                    agent,
                    {"messages": [HumanMessage(content=message)]},
                    run_config,
                    on_event=on_agent_event,
                    on_todos_update=on_todos_update,
                    initial_tokens=session_tokens,
                    run_context=run_context,
                )
            except httpx.TimeoutException as exc:
                logger.warning(
                    "orchestrator LLM timeout",
                    extra={"attempt": attempt, "timeout_s": config.llm_request_timeout},
                )
                if attempt >= config.agent_max_attempts:
                    raise OrchestratorError(_llm_timeout_error_message(config)) from exc
                if on_retry is not None:
                    on_retry(attempt + 1, config.agent_max_attempts)
                continue
            run_context.orchestrator_tokens = session_tokens

            current_snapshot = _artifact_files(workspace)
            current_notes = _review_notes_count(workspace)
            if not _missing_artifacts(workspace):
                break
            if current_snapshot == last_snapshot and current_notes == last_notes:
                logger.warning(
                    "orchestrator attempt made no progress",
                    extra={"attempt": attempt},
                )
            last_snapshot = current_snapshot
            last_notes = current_notes
    except GraphRecursionError as exc:
        logger.warning(
            "orchestrator recursion limit reached",
            extra={
                "limit": config.agent_recursion_limit,
                "notes": _review_notes_count(workspace),
            },
        )
        raise OrchestratorError(
            _recursion_limit_error_message(workspace, limit=config.agent_recursion_limit),
        ) from exc
    except Exception as exc:
        logger.exception("orchestrator failed")
        msg = f"ошибка агента: {exc}"
        raise OrchestratorError(msg) from exc

    feedback_path = workspace / "feedback.md"
    if _missing_artifacts(workspace):
        raise OrchestratorError(_artifact_error_message(workspace))

    return feedback_path
