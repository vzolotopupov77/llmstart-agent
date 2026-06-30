"""Tests for GlobalRetriever with mocked Neo4j driver."""

from unittest.mock import MagicMock

import pytest

from mcp_server.retriever.global_agg import GlobalRetriever, _match_template


def _mock_driver(records: list[dict[str, object]]) -> MagicMock:
    driver = MagicMock()
    driver.execute_query.return_value = (records, None, None)
    return driver


def test_match_template_mcp_courses() -> None:
    assert _match_template("В каких курсах каталога встречается тема MCP?") == "theme_courses"


@pytest.mark.parametrize(
    "query",
    [
        "В каких курсах каталога встречается тема MCP?",
        "Какие курсы покрывают тему MCP?",
        "Где изучается Model Context Protocol?",
    ],
)
def test_match_template_theme_rephrasings(query: str) -> None:
    assert _match_template(query) == "theme_courses"


def test_global_theme_courses(settings_env: object) -> None:
    driver = _mock_driver(
        [
            {"courseId": "fullstack-aidd", "title": "Fullstack", "themeId": "mcp"},
            {"courseId": "agents", "title": "Agents", "themeId": "mcp"},
            {"courseId": "deep-agents", "title": "Deep Agents", "themeId": "mcp"},
        ],
    )
    retriever = GlobalRetriever(driver=driver)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "mcp_server.retriever.global_agg.ensure_graph_ready",
        lambda _driver: None,
    )
    try:
        chunks = retriever.search(
            "В каких курсах каталога встречается тема MCP?",
            "b2c",
            top_k=3,
        )
    finally:
        monkeypatch.undo()

    text = chunks[0]["text"]
    assert "fullstack-aidd" in text
    assert "agents" in text
    assert "deep-agents" in text
    assert chunks[0]["branch"] == "global"


def test_global_authors_gap(settings_env: object) -> None:
    retriever = GlobalRetriever(driver=_mock_driver([]))
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "mcp_server.retriever.global_agg.ensure_graph_ready",
        lambda _driver: None,
    )
    try:
        chunks = retriever.search("Кто ведёт курсы в каталоге LLMStart?", "b2c", top_k=1)
    finally:
        monkeypatch.undo()

    assert "authors" in chunks[0]["text"]
