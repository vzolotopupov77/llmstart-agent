"""Reviewer-субагент: изолированная проверка одного аспекта рубрики."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError

from mentor.brief import (
    BriefError,
    estimate_tokens,
    parse_aspect_from_brief_path,
    resolve_aspect_id,
)
from mentor.config import CONFIG_DIR, AppConfig
from mentor.openrouter import build_chat_model
from mentor.prompts import PromptLoadError, load_yaml_prompt

logger = logging.getLogger(__name__)

REVIEWER_RECURSION_LIMIT = 100
REVIEWER_MAX_ATTEMPTS = 5


class ReviewerError(Exception):
    """Ошибка выполнения Reviewer-субагента."""


@dataclass(frozen=True)
class ReviewerResult:
    """Результат запуска Reviewer-субагента."""

    aspect: str
    note_path: Path
    subagent_context_tokens: int


def _normalize_workspace_path(path: Path | str, workspace: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(workspace)
        except ValueError:
            msg = f"путь вне workspace: {candidate.as_posix()}"
            raise ReviewerError(msg) from None
    return candidate


def _extract_max_tokens(messages: list[BaseMessage]) -> int:
    max_tokens = 0
    for message in messages:
        if not isinstance(message, AIMessage):
            continue
        usage = getattr(message, "usage_metadata", None)
        if not isinstance(usage, dict):
            continue
        input_tokens = usage.get("input_tokens")
        if isinstance(input_tokens, int) and input_tokens > max_tokens:
            max_tokens = input_tokens
    return max_tokens


def _build_reviewer_message(brief_path: Path, note_path: Path, aspect: str) -> str:
    return (
        f"Проверь аспект `{aspect}` по брифу `{brief_path.as_posix()}`.\n\n"
        f"Запиши ReviewNote в `{note_path.as_posix()}` "
        f"с секциями `## findings` и `## recommendations`.\n\n"
        "Начни с read_file брифа, затем читай только указанные файлы с префиксом `code/`.\n"
        "Не отвечай текстом без tool call, пока ReviewNote не записан через write_file."
    )


def _build_continue_message(note_path: Path) -> str:
    return (
        f"ReviewNote `{note_path.as_posix()}` ещё не создан или неполный.\n\n"
        "Следующий шаг — вызови write_file и запиши секции `## findings` и "
        "`## recommendations`.\n"
        "Не отвечай текстом без tool call."
    )


def _review_note_is_valid(path: Path) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8").lower()
    return "## findings" in content and "## recommendations" in content


def _locate_review_note(workspace: Path, aspect: str) -> Path | None:
    """Найти ReviewNote; допускает альтернативное имя от модели."""
    expected = workspace / "notes" / f"review-{aspect}.md"
    if _review_note_is_valid(expected):
        return Path("notes") / f"review-{aspect}.md"

    notes_dir = workspace / "notes"
    if not notes_dir.exists():
        return None

    candidates = sorted(notes_dir.glob("review-*.md"), key=lambda item: item.stat().st_mtime)
    aspect_tokens = {aspect, aspect.replace("-", "_")}
    for path in reversed(candidates):
        stem = path.stem.removeprefix("review-")
        if stem in aspect_tokens and _review_note_is_valid(path):
            return Path("notes") / path.name
    return None


def run_reviewer(brief_path: Path, workspace: Path, config: AppConfig) -> ReviewerResult:
    """Запустить Reviewer-субагента для одного брифа."""
    os.environ["OPENROUTER_API_KEY"] = config.openrouter_api_key

    brief_relative = _normalize_workspace_path(brief_path, workspace)
    if not (workspace / brief_relative).exists():
        msg = f"бриф не найден: {brief_relative.as_posix()}"
        raise ReviewerError(msg)

    try:
        raw_aspect = parse_aspect_from_brief_path(brief_relative)
        aspect = resolve_aspect_id(raw_aspect, workspace / "rubric.md")
    except BriefError as exc:
        raise ReviewerError(str(exc)) from exc

    note_path = Path("notes") / f"review-{aspect}.md"
    notes_dir = workspace / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = CONFIG_DIR / "prompts" / "reviewer-system.yaml"
    try:
        system_prompt = load_yaml_prompt(prompt_path)
    except PromptLoadError as exc:
        raise ReviewerError(str(exc)) from exc

    backend = FilesystemBackend(root_dir=workspace, virtual_mode=True)
    compiled_agent: Any = create_deep_agent(
        model=build_chat_model(config),
        backend=backend,
        system_prompt=system_prompt,
        checkpointer=MemorySaver(),
    )

    thread_id = uuid4().hex
    run_config: dict[str, Any] = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": REVIEWER_RECURSION_LIMIT,
    }

    logger.info(
        "reviewer started",
        extra={"aspect": aspect, "brief": brief_relative.as_posix()},
    )

    result: dict[str, Any] | Any = {}
    last_snapshot = _review_note_is_valid(workspace / note_path)

    try:
        for attempt in range(1, REVIEWER_MAX_ATTEMPTS + 1):
            if attempt == 1:
                message = _build_reviewer_message(brief_relative, note_path, aspect)
            elif not last_snapshot:
                thread_id = uuid4().hex
                run_config["configurable"]["thread_id"] = thread_id
                message = (
                    f"{_build_reviewer_message(brief_relative, note_path, aspect)}\n\n"
                    f"{_build_continue_message(note_path)}"
                )
                logger.warning(
                    "reviewer fresh retry",
                    extra={"attempt": attempt, "aspect": aspect},
                )
            else:
                message = _build_continue_message(note_path)

            if attempt > 1:
                logger.warning(
                    "reviewer retry",
                    extra={"attempt": attempt, "aspect": aspect},
                )

            result = compiled_agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=run_config,
            )

            located = _locate_review_note(workspace, aspect)
            if located is not None:
                note_path = located
                break

            if _review_note_is_valid(workspace / note_path):
                break

            logger.warning(
                "reviewer attempt made no progress",
                extra={"attempt": attempt, "aspect": aspect},
            )
            last_snapshot = False
    except GraphRecursionError as exc:
        located = _locate_review_note(workspace, aspect)
        if located is not None:
            note_path = located
        else:
            msg = (
                f"reviewer `{aspect}` не завершился: исчерпан лимит шагов "
                f"({REVIEWER_RECURSION_LIMIT})"
            )
            raise ReviewerError(msg) from exc
    except Exception as exc:
        located = _locate_review_note(workspace, aspect)
        if located is not None:
            note_path = located
        else:
            msg = f"reviewer `{aspect}` завершился с ошибкой: {exc}"
            raise ReviewerError(msg) from exc

    target = workspace / note_path
    if not _review_note_is_valid(target):
        msg = (
            f"reviewer `{aspect}` не создал {note_path.as_posix()} "
            f"за {REVIEWER_MAX_ATTEMPTS} попыток"
        )
        raise ReviewerError(msg)

    content = target.read_text(encoding="utf-8")
    messages = result.get("messages", []) if isinstance(result, dict) else []
    parsed_messages = [msg for msg in messages if isinstance(msg, BaseMessage)]
    subagent_tokens = _extract_max_tokens(parsed_messages)
    if subagent_tokens == 0:
        subagent_tokens = estimate_tokens(content)

    logger.info(
        "reviewer completed",
        extra={
            "aspect": aspect,
            "note": note_path.as_posix(),
            "tokens": subagent_tokens,
        },
    )
    return ReviewerResult(
        aspect=aspect,
        note_path=note_path,
        subagent_context_tokens=subagent_tokens,
    )
