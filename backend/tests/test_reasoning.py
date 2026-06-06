"""Tests for operational reasoning trace (not final user message)."""

from langchain_core.messages import AIMessage, ToolMessage

from app.agent.react_runner import ToolCallRecord, _build_reasoning, _parse_turn


def test_build_reasoning_uses_tool_steps_not_final_answer() -> None:
    reasoning = _build_reasoning(
        [],
        [
            ToolCallRecord(name="list_b2c_products", status="done", title="Каталог курсов"),
        ],
    )

    assert "Каталог курсов" in reasoning
    assert "Формирование рекомендации" in reasoning
    assert "Анализ запроса" in reasoning


def test_parse_turn_reasoning_differs_from_final_message() -> None:
    turn = _parse_turn(
        [
            AIMessage(
                content="",
                tool_calls=[{"name": "list_b2c_products", "args": {}, "id": "1"}],
            ),
            ToolMessage(content='{"items": []}', name="list_b2c_products", tool_call_id="1"),
            AIMessage(content="Для новичка рекомендую курс agents по LangChain."),
        ],
    )

    assert turn.final_message == "Для новичка рекомендую курс agents по LangChain."
    assert turn.final_message not in turn.reasoning
    assert "Вызов инструмента: Каталог курсов" in turn.reasoning
    assert "Формирование рекомендации" in turn.reasoning
