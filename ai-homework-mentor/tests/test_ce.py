"""Тесты Context Engineering helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from deepagents.backends import FilesystemBackend
from langchain.agents.middleware.types import ExtendedModelResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from mentor.agent import AgentRunContext
from mentor.ce import (
    build_ce_middleware,
    build_summarization_ce_event,
    ce_keep_tokens,
    compaction_overflow_threshold,
    estimate_text_tokens,
    format_compaction_overflow_trigger,
    make_write_to_workspace_tool,
)
from mentor.config import AppConfig
from mentor.events import CompactionEvent, FileOffloadEvent, SummarizationEvent
from mentor.openrouter import build_chat_model
from mentor.parser import Submission


def _app_config(
    monkeypatch: pytest.MonkeyPatch,
    *,
    summarization_threshold: int = 80_000,
    context_limit: int = 128_000,
) -> AppConfig:
    """Конфиг для CE-тестов — не зависит от локального .env."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("SUMMARIZATION_THRESHOLD", str(summarization_threshold))
    monkeypatch.setenv("CONTEXT_LIMIT", str(context_limit))
    return AppConfig()


def test_estimate_text_tokens() -> None:
    assert estimate_text_tokens("") == 0
    assert estimate_text_tokens("abcd") == 1


def test_ce_keep_tokens_stays_below_threshold() -> None:
    for threshold in (5_000, 80_000, 128_000):
        keep = ce_keep_tokens(threshold)
        assert keep < threshold
        assert keep >= 400


def test_build_ce_middleware_can_evict_messages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Регрессия: keep=fraction от 1M max_input_tokens давал cutoff=0."""
    config = _app_config(monkeypatch, summarization_threshold=5_000)
    model = build_chat_model(config)
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    summarization = build_ce_middleware(model, backend, config)[0]

    chunk = "context " * 800
    messages = [HumanMessage(content=chunk) for _ in range(4)]
    total_tokens = summarization.token_counter(messages)
    assert total_tokens >= config.summarization_threshold
    assert summarization._should_summarize(messages, total_tokens)  # noqa: SLF001
    assert summarization._determine_cutoff_index(messages) > 0  # noqa: SLF001


def test_build_summarization_ce_event(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _app_config(monkeypatch)
    raw = {
        "cutoff_index": 5,
        "file_path": "/conversation_history/t.md",
        "summary_message": None,
    }
    event = build_summarization_ce_event(raw, tokens_before=12_000, config=config)
    assert isinstance(event, SummarizationEvent)
    assert event.tokens_before == 12_000
    assert event.tokens_after < event.tokens_before


def test_build_summarization_ce_event_overflow_is_compaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _app_config(monkeypatch, context_limit=12_000, summarization_threshold=10_000)
    raw = {
        "cutoff_index": 5,
        "file_path": "/conversation_history/t.md",
        "summary_message": None,
    }
    event = build_summarization_ce_event(raw, tokens_before=10_339, config=config)
    assert isinstance(event, CompactionEvent)
    assert event.trigger == format_compaction_overflow_trigger(12_000)
    assert compaction_overflow_threshold(12_000) == 10_200


def test_reporting_middleware_invokes_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _app_config(monkeypatch)
    model = build_chat_model(config)
    backend = FilesystemBackend(root_dir=tmp_path, virtual_mode=True)
    seen: list[dict[str, object]] = []

    middleware = build_ce_middleware(
        model,
        backend,
        config,
        on_summarization=seen.append,
    )[0]

    raw_event = {
        "cutoff_index": 3,
        "file_path": "/conversation_history/x.md",
        "summary_message": HumanMessage(content="summary"),
    }
    response = ExtendedModelResponse(
        model_response={"messages": []},  # type: ignore[arg-type]
        command=Command(update={"_summarization_event": raw_event}),
    )
    middleware._report(response)  # noqa: SLF001

    assert len(seen) == 1
    assert seen[0]["cutoff_index"] == 3


def test_write_to_workspace_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _app_config(monkeypatch)
    events: list[FileOffloadEvent] = []

    def on_ce_event(event: FileOffloadEvent) -> None:
        events.append(event)

    ctx = AgentRunContext(
        workspace=tmp_path,
        config=config,
        submission=Submission(source_type="local", source="/tmp", topic="test"),
        on_event=on_ce_event,
    )
    tool = make_write_to_workspace_tool(ctx)
    result = tool.invoke(
        {
            "content": "x" * 400,
            "filename": "scratch/synthesis-notes.md",
            "summary": "Краткие выводы по 4 аспектам",
        },
    )

    target = tmp_path / "scratch" / "synthesis-notes.md"
    assert target.exists()
    assert "scratch/synthesis-notes.md" in result
    assert len(events) == 1
    assert events[0].filename == "scratch/synthesis-notes.md"
    assert events[0].savings > 0
