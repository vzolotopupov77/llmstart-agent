"""Unit-тесты subagent-событий трекера."""

from __future__ import annotations

from pathlib import Path

from langchain_core.messages import AIMessage

from mentor.agent import AgentRunContext
from mentor.config import AppConfig
from mentor.events import SubagentEndEvent, SubagentStartEvent
from mentor.parser import Submission
from mentor.tracker import _process_stream_update, _StreamTrackerState


def test_subagent_end_emitted_after_context_update(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    ctx = AgentRunContext(
        workspace=workspace,
        config=AppConfig(openrouter_api_key="test-key"),
        submission=Submission(source_type="local", source="/tmp", topic="test"),
        orchestrator_tokens=10_000,
    )
    ctx.pending_subagent = SubagentStartEvent(
        aspect="structure",
        brief_path="briefs/brief-structure.md",
        brief_tokens=180,
    )
    ctx.pending_subagent_result = ("notes/review-structure.md", 4100)
    ctx.spawn_orchestrator_tokens_before = 10_000

    state = _StreamTrackerState(tokens_after=10_000)
    events: list[object] = []

    def emit(event: object) -> None:
        events.append(event)

    message = AIMessage(
        content="",
        usage_metadata={"input_tokens": 10_200, "output_tokens": 50, "total_tokens": 10_250},
    )
    _process_stream_update({"messages": [message]}, emit=emit, state=state, run_context=ctx)

    end_events = [event for event in events if isinstance(event, SubagentEndEvent)]
    assert len(end_events) == 1
    assert end_events[0].orchestrator_delta == 200
    assert end_events[0].savings == 4300
    assert ctx.pending_subagent is None
