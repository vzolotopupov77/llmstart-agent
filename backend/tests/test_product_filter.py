"""Tests for recommended product filtering."""

from app.agent.product_filter import filter_recommended_products

ProductDict = dict[str, str | int]


def test_filters_by_product_code() -> None:
    items: list[ProductDict] = [
        {"code": "agents", "title": "Базовый курс по ИИ-агентам", "price": 1, "currency": "RUB"},
        {"code": "deep-agents", "title": "Продвинутый курс", "price": 2, "currency": "RUB"},
    ]

    result = filter_recommended_products(
        items,
        "Для новичка рекомендую курс agents — введение в LangChain.",
    )

    assert result is not None
    assert len(result) == 1
    assert result[0]["code"] == "agents"


def test_filters_by_title() -> None:
    items: list[ProductDict] = [
        {"code": "agents", "title": "Базовый курс по ИИ-агентам", "price": 1, "currency": "RUB"},
        {
            "code": "deep-agents",
            "title": "Продвинутый курс Deep Agents",
            "price": 2,
            "currency": "RUB",
        },
    ]

    result = filter_recommended_products(
        items,
        "Подойдёт «Базовый курс по ИИ-агентам» для старта.",
    )

    assert result is not None
    assert result[0]["code"] == "agents"


def test_returns_none_when_nothing_referenced() -> None:
    items: list[ProductDict] = [
        {"code": "agents", "title": "Базовый курс", "price": 1, "currency": "RUB"},
    ]

    assert filter_recommended_products(items, "Вот несколько вариантов для вас.") is None


def test_limits_to_max_items() -> None:
    items: list[ProductDict] = [
        {"code": "agents", "title": "A", "price": 1, "currency": "RUB"},
        {"code": "deep-agents", "title": "B", "price": 2, "currency": "RUB"},
        {"code": "fullstack-aidd", "title": "C", "price": 3, "currency": "RUB"},
        {"code": "consultation", "title": "D", "price": 4, "currency": "RUB"},
    ]

    result = filter_recommended_products(
        items,
        "Рекомендую agents, deep-agents и fullstack-aidd для разного уровня.",
        max_items=2,
    )

    assert result is not None
    assert len(result) == 2
