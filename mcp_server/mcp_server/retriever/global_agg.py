"""Global catalog aggregation retrieval via Neo4j Cypher."""

from __future__ import annotations

from neo4j import Driver

from mcp_server.retriever.base import KnowledgeChunk, Segment
from mcp_server.retriever.graph_entities import THEME_KEYWORDS
from mcp_server.retriever.neo4j_driver import ensure_graph_ready, get_neo4j_driver


def _format_global_chunk(
    *,
    text: str,
    entity_id: str,
    segment: Segment,
) -> KnowledgeChunk:
    return {
        "text": text,
        "source": "neo4j/global",
        "segment": segment,
        "branch": "global",
        "entity_id": entity_id,
    }


def _match_template(query: str) -> str:
    lowered = query.lower()
    if any(word in lowered for word in ("автор", "ведёт", "ведет", "преподав")):
        return "authors_gap"
    if any(word in lowered for word in ("ак.", "академ", "нагруз", "часов")):
        return "hours_sum"
    if "формат" in lowered:
        return "formats"
    if any(word in lowered for word in ("менедж", "продакт", "без кода", "non-dev")):
        return "audience"
    if _is_theme_courses_query(lowered):
        return "theme_courses"
    if "сколько" in lowered and "курс" in lowered:
        return "course_count"
    return "catalog_snapshot"


def _is_theme_courses_query(lowered: str) -> bool:
    theme_phrases = (
        "в каких курсах",
        "встречается",
        "есть тема",
        "каталоге встреча",
        "покрывают тему",
        "покрывает тему",
        "где изуча",
        "где проходит",
        "model context protocol",
    )
    if any(phrase in lowered for phrase in theme_phrases):
        return True
    return _detect_theme_id(lowered) is not None and any(
        marker in lowered for marker in ("тема", "тему", "темы", "topic")
    )


def _detect_theme_id(query: str) -> str | None:
    lowered = query.lower()
    if "model context protocol" in lowered:
        return "mcp"
    for keyword, theme_id in THEME_KEYWORDS.items():
        if keyword in lowered:
            return theme_id
    return None


class GlobalRetriever:
    """Structural catalog aggregates without vector search."""

    def __init__(self, *, driver: Driver | None = None) -> None:
        self._driver = driver

    def _driver_or_cached(self) -> Driver:
        return self._driver or get_neo4j_driver()

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        if segment not in ("b2b", "b2c"):
            msg = f"invalid segment: {segment}"
            raise ValueError(msg)

        driver = self._driver_or_cached()
        ensure_graph_ready(driver)
        template = _match_template(query)

        if template == "authors_gap":
            return [
                _format_global_chunk(
                    text=(
                        "[global] authors | note=данные об авторах не в графе "
                        "(Instructor node deferred); consult program pages"
                    ),
                    entity_id="authors-gap",
                    segment=segment,
                ),
            ]
        if template == "hours_sum":
            return self._hours_sum(driver, segment=segment)[:top_k]
        if template == "formats":
            return self._formats(driver, segment=segment)[:top_k]
        if template == "audience":
            return self._audience_courses(driver, segment=segment)[:top_k]
        if template == "theme_courses":
            theme_id = _detect_theme_id(query)
            if theme_id:
                return self._theme_courses(driver, theme_id, segment=segment)[:top_k]
            return self._theme_unknown(driver, segment=segment)[:top_k]
        if template == "course_count":
            return self._course_count(driver, segment=segment)[:top_k]
        return self._catalog_snapshot(driver, segment=segment)[:top_k]

    def _run(
        self,
        driver: Driver,
        cypher: str,
        parameters: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        records, _, _ = driver.execute_query(cypher, parameters or {}, database_="neo4j")
        return [dict(record) for record in records]

    def _course_count(self, driver: Driver, *, segment: Segment) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (c:Course)
            WHERE c.segment = $segment OR c.segment = 'both'
            RETURN count(c) AS total,
                   collect({id: c.id, title: c.title, priceRub: c.priceRub}) AS courses
            """,
            {"segment": segment},
        )
        row = rows[0] if rows else {"total": 0, "courses": []}
        return [
            _format_global_chunk(
                text=(
                    f"[global] course_count | total={row.get('total')} | "
                    f"courses={row.get('courses')}"
                ),
                entity_id="global:course-count",
                segment=segment,
            ),
        ]

    def _formats(self, driver: Driver, *, segment: Segment) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (f:Format)<-[:AVAILABLE_AS]-(c:Course)
            WHERE c.segment = $segment OR c.segment = 'both'
            RETURN DISTINCT f.id AS formatId, f.name AS formatName,
                   collect(DISTINCT c.id) AS courses
            ORDER BY f.id
            """,
            {"segment": segment},
        )
        formats = [
            {
                "id": row.get("formatId"),
                "name": row.get("formatName"),
                "courses": row.get("courses"),
            }
            for row in rows
        ]
        return [
            _format_global_chunk(
                text=f"[global] formats | items={formats}",
                entity_id="global:formats",
                segment=segment,
            ),
        ]

    def _theme_courses(
        self,
        driver: Driver,
        theme_id: str,
        *,
        segment: Segment,
    ) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (c:Course)-[:COVERS]->(t:Theme)
            WHERE t.id = $themeId OR $themeId IN coalesce(t.aliases, [])
            RETURN c.id AS courseId, c.title AS title, t.id AS themeId
            ORDER BY c.id
            """,
            {"themeId": theme_id},
        )
        courses = [{"id": row.get("courseId"), "title": row.get("title")} for row in rows]
        return [
            _format_global_chunk(
                text=f"[global] theme_courses | theme={theme_id} | courses={courses}",
                entity_id=f"global:theme:{theme_id}",
                segment=segment,
            ),
        ]

    def _audience_courses(self, driver: Driver, *, segment: Segment) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (c:Course)-[:TARGETS]->(a:Audience {id: 'non-dev'})
            RETURN c.id AS courseId, c.title AS title, c.priceRub AS priceRub, c.level AS level
            ORDER BY c.priceRub
            """,
        )
        courses = [dict(row) for row in rows]
        return [
            _format_global_chunk(
                text=f"[global] audience=non-dev | courses={courses}",
                entity_id="global:audience:non-dev",
                segment=segment,
            ),
        ]

    def _theme_unknown(self, driver: Driver, *, segment: Segment) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (t:Theme)
            WITH t ORDER BY t.id
            RETURN collect({id: t.id, name: t.name}) AS themes
            """,
        )
        themes = rows[0].get("themes") if rows else []
        return [
            _format_global_chunk(
                text=(
                    "[global] theme_courses | note=theme_not_detected_in_query | "
                    f"available_themes={themes}"
                ),
                entity_id="global:theme-unknown",
                segment=segment,
            ),
        ]

    def _hours_sum(self, driver: Driver, *, segment: Segment) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (cb:Combo {id: 'ai-agents-combo'})-[:INCLUDES]->(c:Course)
            WITH cb, c
            WHERE c.academicHours IS NOT NULL
            RETURN cb.id AS comboId,
                   collect({id: c.id, title: c.title, hours: c.academicHours}) AS courses,
                   sum(c.academicHours) AS totalHours
            """,
        )
        row = rows[0] if rows else {}
        return [
            _format_global_chunk(
                text=(
                    f"[global] combo_hours | combo={row.get('comboId')} | "
                    f"courses={row.get('courses')} | totalHours={row.get('totalHours')}"
                ),
                entity_id="global:combo-hours",
                segment=segment,
            ),
        ]

    def _catalog_snapshot(self, driver: Driver, *, segment: Segment) -> list[KnowledgeChunk]:
        course_rows = self._run(
            driver,
            """
            MATCH (c:Course)
            WHERE c.segment = $segment OR c.segment = 'both'
            RETURN collect({id: c.id, title: c.title, priceRub: c.priceRub}) AS courses
            """,
            {"segment": segment},
        )
        combo_rows = self._run(
            driver,
            "MATCH (cb:Combo) RETURN collect({id: cb.id, title: cb.title}) AS combos",
        )
        courses_raw = course_rows[0].get("courses") if course_rows else []
        courses = courses_raw if isinstance(courses_raw, list) else []
        combos_raw = combo_rows[0].get("combos") if combo_rows else []
        combos = combos_raw if isinstance(combos_raw, list) else []
        return [
            _format_global_chunk(
                text=(
                    f"[global] catalog_summary | courses={courses} | combos={combos} | "
                    f"courseCount={len(courses)}"
                ),
                entity_id="global:catalog",
                segment=segment,
            ),
        ]
