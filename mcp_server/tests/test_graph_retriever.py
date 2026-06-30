"""Tests for GraphRetriever with mocked Neo4j driver."""

from unittest.mock import MagicMock

import pytest

from mcp_server.retriever.graph import GraphRetriever
from tests.mocks import MockRetriever


def _mock_driver(records: list[dict[str, object]]) -> MagicMock:
    driver = MagicMock()
    driver.execute_query.return_value = (records, None, None)
    return driver


def test_graph_prerequisite_chain(settings_env: object) -> None:
    driver = _mock_driver(
        [
            {
                "courseId": "deep-agents",
                "title": "Deep Agents",
                "priceRub": 44990,
                "prereqChains": [["vibe-coding", "fullstack-aidd", "agents"]],
                "themes": ["graphrag"],
            },
        ],
    )
    retriever = GraphRetriever(vector=MockRetriever(), driver=driver)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "mcp_server.retriever.graph.ensure_graph_ready",
        lambda _driver: None,
    )
    try:
        chunks = retriever.search(
            "Что нужно пройти перед курсом Deep Agents?",
            "b2c",
            top_k=3,
        )
    finally:
        monkeypatch.undo()

    assert chunks
    text = chunks[0]["text"]
    assert "vibe-coding" in text
    assert "agents" in text
    assert chunks[0]["branch"] == "graph"


def test_graph_intersection(settings_env: object) -> None:
    driver = _mock_driver(
        [
            {"themeId": "mcp", "themeName": "MCP"},
            {"themeId": "observability", "themeName": "Observability"},
        ],
    )
    retriever = GraphRetriever(vector=MockRetriever(), driver=driver)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        "mcp_server.retriever.graph.ensure_graph_ready",
        lambda _driver: None,
    )
    try:
        chunks = retriever.search(
            "Что общего в темах курсов fullstack-aidd и agents?",
            "b2c",
            top_k=3,
        )
    finally:
        monkeypatch.undo()

    assert chunks
    assert "mcp" in chunks[0]["text"]
