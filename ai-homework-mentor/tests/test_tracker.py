"""Unit-тесты трекера контекста."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from mentor.events import CompactionEvent, ContextEvent, SummarizationEvent
from mentor.tracker import (
    _process_stream_update,
    _StreamTrackerState,
    extract_file_events_from_message,
    extract_file_paths,
    extract_input_tokens,
    extract_tokens_from_message,
    format_files_preview,
    is_outside_student_code,
)


def test_extract_tokens_from_message() -> None:
    message = AIMessage(
        content="ok",
        usage_metadata={"input_tokens": 5100, "output_tokens": 40, "total_tokens": 5140},
    )

    assert extract_tokens_from_message(message) == 5100


def test_extract_file_events_from_tool_calls() -> None:
    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "read_file",
                "args": {"file_path": "code/main.py"},
                "id": "call_1",
                "type": "tool_call",
            },
        ],
    )

    events = extract_file_events_from_message(message)

    assert len(events) == 1
    assert events[0].path == "code/main.py"
    assert events[0].tool_name == "read_file"


def test_extract_input_tokens_from_usage_metadata() -> None:
    message = AIMessage(
        content="ok",
        usage_metadata={"input_tokens": 4200, "output_tokens": 50, "total_tokens": 4250},
    )
    result = LLMResult(generations=[[ChatGeneration(message=message)]])

    assert extract_input_tokens(result) == 4200


def test_extract_input_tokens_from_llm_output() -> None:
    result = LLMResult(
        generations=[[]],
        llm_output={"token_usage": {"prompt_tokens": 3100, "completion_tokens": 10}},
    )

    assert extract_input_tokens(result) == 3100


def test_extract_file_paths_read_file() -> None:
    paths = extract_file_paths("read_file", {"file_path": "code/main.py"})

    assert paths == ["code/main.py"]


def test_extract_file_paths_grep() -> None:
    paths = extract_file_paths(
        "grep",
        {"pattern": "def", "path": "code/", "include": "*.py"},
    )

    assert paths == ["code/", "*.py"]


def test_is_outside_student_code() -> None:
    assert is_outside_student_code("README.md") is True
    assert is_outside_student_code("/submission.md") is False
    assert is_outside_student_code("code/README.md") is False
    assert is_outside_student_code("code-index.md") is False
    assert is_outside_student_code("notes/review-structure.md") is False


def test_context_tokens_continue_between_llm_calls() -> None:
    state = _StreamTrackerState()
    events: list[ContextEvent] = []

    def emit(event: object) -> None:
        if isinstance(event, ContextEvent):
            events.append(event)

    first = AIMessage(
        content="",
        usage_metadata={"input_tokens": 10_000, "output_tokens": 100, "total_tokens": 10_100},
    )
    second = AIMessage(
        content="",
        usage_metadata={"input_tokens": 12_000, "output_tokens": 100, "total_tokens": 12_100},
    )

    _process_stream_update({"messages": [first]}, emit=emit, state=state)
    _process_stream_update({"messages": [second]}, emit=emit, state=state)

    assert len(events) == 2
    assert events[1].tokens_before == 10_000
    assert events[1].tokens_after == 12_000
    assert events[1].delta == 2_000


def test_context_tokens_reset_on_fresh_thread() -> None:
    state = _StreamTrackerState(tokens_after=30_000)
    events: list[ContextEvent] = []

    def emit(event: object) -> None:
        if isinstance(event, ContextEvent):
            events.append(event)

    message = AIMessage(
        content="",
        usage_metadata={"input_tokens": 6_000, "output_tokens": 50, "total_tokens": 6_050},
    )
    _process_stream_update({"messages": [message]}, emit=emit, state=state)

    assert events[0].tokens_before == 0
    assert events[0].tokens_after == 6_000


def test_context_event_delta() -> None:
    event = ContextEvent(
        step="Чтение кода",
        tokens_before=1200,
        tokens_after=9600,
        files_read=["code-index.md"],
    )

    assert event.delta == 8400


def test_format_files_preview_truncates() -> None:
    files = ["a.py", "b.py", "c.py", "d.py", "e.py"]
    preview = format_files_preview(files, limit=3)

    assert "a.py" in preview
    assert "(+2 файл)" in preview


def test_on_todos_update_called_from_stream_update() -> None:
    state = _StreamTrackerState()
    seen: list[list[dict[str, str]]] = []

    def on_todos_update(todos: list[dict[str, str]]) -> None:
        seen.append(todos)

    _process_stream_update(
        {
            "todos": [
                {"content": "Читаю rubric.md", "status": "in_progress"},
                {"content": "Синтез feedback", "status": "pending"},
            ],
        },
        emit=lambda _event: None,
        state=state,
        on_todos_update=on_todos_update,
    )

    assert len(seen) == 1
    assert seen[0][0]["content"] == "Читаю rubric.md"


def test_summarization_event_emits_immediately() -> None:
    state = _StreamTrackerState(tokens_after=90_000)
    events: list[SummarizationEvent | CompactionEvent] = []

    def emit(event: object) -> None:
        if isinstance(event, (SummarizationEvent, CompactionEvent)):
            events.append(event)

    _process_stream_update(
        {"_summarization_event": {"cutoff_index": 12, "file_path": "/conversation_history/t1.md"}},
        emit=emit,
        state=state,
    )

    assert len(events) == 1
    assert isinstance(events[0], SummarizationEvent)
    assert events[0].tokens_before == 90_000
    assert events[0].tokens_after < 90_000
    assert events[0].history_file == "/conversation_history/t1.md"


def test_summarization_event_without_token_drop() -> None:
    """usage_metadata может расти после суммаризации — панель всё равно появляется."""
    state = _StreamTrackerState(tokens_after=18_000)
    events: list[SummarizationEvent] = []

    def emit(event: object) -> None:
        if isinstance(event, SummarizationEvent):
            events.append(event)

    _process_stream_update(
        {
            "model": {
                "_summarization_event": {
                    "cutoff_index": 8,
                    "file_path": "/conversation_history/thread-a.md",
                    "summary_message": HumanMessage(content="Summary of prior steps."),
                },
            },
        },
        emit=emit,
        state=state,
    )

    growing = AIMessage(
        content="",
        usage_metadata={"input_tokens": 25_000, "output_tokens": 50, "total_tokens": 25_050},
    )
    _process_stream_update({"messages": [growing]}, emit=emit, state=state)

    assert len(events) == 1
    assert events[0].tokens_before == 18_000
    assert events[0].tokens_after < events[0].tokens_before


def test_summarization_event_deduplicates_by_signature() -> None:
    state = _StreamTrackerState(tokens_after=10_000)
    events: list[SummarizationEvent] = []

    def emit(event: object) -> None:
        if isinstance(event, SummarizationEvent):
            events.append(event)

    payload = {"cutoff_index": 3, "file_path": "/conversation_history/t.md"}
    _process_stream_update({"_summarization_event": payload}, emit=emit, state=state)
    _process_stream_update({"_summarization_event": payload}, emit=emit, state=state)

    assert len(events) == 1
