"""Tests for graph entity resolution."""

from mcp_server.retriever.graph_entities import extract_entities, resolve_course_id_from_payload


def test_extract_prerequisite_target_course() -> None:
    entities = extract_entities("Что нужно пройти перед курсом Deep Agents?")
    assert "deep-agents" in entities.course_ids


def test_extract_intersection_pair() -> None:
    entities = extract_entities("Что общего в темах курсов fullstack-aidd и agents?")
    assert entities.intersection_pair == ("fullstack-aidd", "agents")


def test_extract_combo_slug() -> None:
    entities = extract_entities("Какие темы охватывает комбо ИИ-агенты?")
    assert "ai-agents-combo" in entities.combo_ids


def test_resolve_course_id_from_source() -> None:
    assert resolve_course_id_from_payload(source="deep-agents-advanced.md") == "deep-agents"
