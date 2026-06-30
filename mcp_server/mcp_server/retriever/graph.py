"""Graph-augmented retrieval: Qdrant anchor + Neo4j Cypher expansion."""

from __future__ import annotations

from typing import cast

from neo4j import Driver

from mcp_server.config import get_settings
from mcp_server.retriever.base import BaseRetriever, KnowledgeChunk, Segment
from mcp_server.retriever.graph_entities import ResolvedEntities, extract_entities
from mcp_server.retriever.neo4j_driver import ensure_graph_ready, get_neo4j_driver


def _format_graph_chunk(
    *,
    text: str,
    entity_id: str,
    segment: Segment,
    source: str = "neo4j/graph",
) -> KnowledgeChunk:
    return {
        "text": text,
        "source": source,
        "segment": segment,
        "branch": "graph",
        "entity_id": entity_id,
    }


def _flatten_prereq_chains(chains: list[list[str] | None]) -> list[str]:
    ordered: list[str] = []
    for chain in chains:
        if not chain:
            continue
        for course_id in chain:
            if course_id not in ordered:
                ordered.append(course_id)
    return ordered


class GraphRetriever:
    """Expand graph context from resolved entities and optional vector anchor."""

    def __init__(
        self,
        *,
        vector: BaseRetriever,
        driver: Driver | None = None,
    ) -> None:
        self._vector = vector
        self._driver = driver

    def _driver_or_cached(self) -> Driver:
        return self._driver or get_neo4j_driver()

    def search(self, query: str, segment: Segment, *, top_k: int) -> list[KnowledgeChunk]:
        if segment not in ("b2b", "b2c"):
            msg = f"invalid segment: {segment}"
            raise ValueError(msg)

        driver = self._driver_or_cached()
        ensure_graph_ready(driver)
        entities = extract_entities(query)
        chunks: list[KnowledgeChunk] = []
        lowered = query.lower()
        is_prereq = "перед" in lowered or "нужно пройти" in lowered

        if entities.intersection_pair and not is_prereq:
            chunks.extend(self._intersection(driver, entities, segment=segment))
        if entities.combo_ids:
            chunks.extend(self._combo_themes(driver, entities.combo_ids[0], segment=segment))
        if is_prereq and entities.course_ids:
            target_id = max(entities.course_ids, key=len)
            chunks.extend(self._prerequisite_chain(driver, target_id, segment=segment))
        elif entities.course_ids:
            for course_id in entities.course_ids:
                chunks.extend(self._course_context(driver, course_id, segment=segment))
        for theme_id in entities.theme_ids:
            chunks.extend(self._theme_routing(driver, theme_id, segment=segment))

        if not chunks:
            chunks.extend(self._anchor_from_vector(query, segment=segment, top_k=top_k))

        seen: set[str] = set()
        unique: list[KnowledgeChunk] = []
        for chunk in chunks:
            key = chunk.get("entity_id") or chunk["text"][:120]
            if key in seen:
                continue
            seen.add(key)
            unique.append(chunk)
        return unique[:top_k]

    def _run(
        self,
        driver: Driver,
        cypher: str,
        parameters: dict[str, object],
    ) -> list[dict[str, object]]:
        records, _, _ = driver.execute_query(cypher, parameters, database_="neo4j")
        return [dict(record) for record in records]

    def _prerequisite_chain(
        self,
        driver: Driver,
        target_id: str,
        *,
        segment: Segment,
    ) -> list[KnowledgeChunk]:
        hops = get_settings().graph_expand_hops
        rows = self._run(
            driver,
            f"""
            MATCH (target:Course {{id: $targetId}})
            OPTIONAL MATCH p = (start:Course)-[:RECOMMENDED_BEFORE*1..{hops}]->(target)
            WHERE NOT ()-[:RECOMMENDED_BEFORE]->(start)
            WITH target,
                 collect(DISTINCT [n IN nodes(p) | n.id]) AS chains
            OPTIONAL MATCH (target)-[:COVERS]->(t:Theme)
            RETURN target.id AS courseId,
                   target.title AS title,
                   target.priceRub AS priceRub,
                   chains AS prereqChains,
                   collect(DISTINCT t.id) AS themes
            """,
            {"targetId": target_id},
        )
        if not rows:
            return []
        row = rows[0]
        chains = row.get("prereqChains") or []
        prereqs = _flatten_prereq_chains(chains if isinstance(chains, list) else [])
        themes = row.get("themes") or []
        text = (
            f"[graph] course={row.get('courseId')} | title={row.get('title')} | "
            f"price={row.get('priceRub')} | prerequisites={prereqs} | themes={themes}"
        )
        return [
            _format_graph_chunk(
                text=text,
                entity_id=str(row.get("courseId", target_id)),
                segment=segment,
            ),
        ]

    def _course_context(
        self,
        driver: Driver,
        course_id: str,
        *,
        segment: Segment,
    ) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (c:Course {id: $courseId})
            OPTIONAL MATCH (c)-[:COVERS]->(t:Theme)
            OPTIONAL MATCH (c)<-[:INCLUDES]-(cb:Combo)
            OPTIONAL MATCH path = (start:Course)-[:RECOMMENDED_BEFORE*1..3]->(c)
            WHERE NOT ()-[:RECOMMENDED_BEFORE]->(start)
            RETURN c.id AS courseId,
                   c.title AS title,
                   c.priceRub AS priceRub,
                   c.level AS level,
                   c.format AS format,
                   collect(DISTINCT t.id) AS themes,
                   collect(DISTINCT cb.id) AS combos,
                   collect(DISTINCT [n IN nodes(path) | n.id]) AS prereqChains
            """,
            {"courseId": course_id},
        )
        if not rows:
            return []
        row = rows[0]
        raw_chains = row.get("prereqChains") or []
        prereqs = _flatten_prereq_chains(cast("list[list[str] | None]", raw_chains))
        text = (
            f"[graph] course={row.get('courseId')} | title={row.get('title')} | "
            f"price={row.get('priceRub')} | level={row.get('level')} | "
            f"format={row.get('format')} | prerequisites={prereqs} | "
            f"themes={row.get('themes')} | combos={row.get('combos')}"
        )
        return [
            _format_graph_chunk(
                text=text,
                entity_id=str(row.get("courseId", course_id)),
                segment=segment,
            ),
        ]

    def _combo_themes(
        self,
        driver: Driver,
        combo_id: str,
        *,
        segment: Segment,
    ) -> list[KnowledgeChunk]:
        rows = self._run(
            driver,
            """
            MATCH (cb:Combo {id: $comboId})-[:INCLUDES]->(c:Course)-[:COVERS]->(t:Theme)
            RETURN cb.id AS comboId,
                   c.id AS courseId,
                   c.title AS title,
                   collect(DISTINCT t.id) AS themes
            ORDER BY c.id
            """,
            {"comboId": combo_id},
        )
        return [
            _format_graph_chunk(
                text=(
                    f"[graph] combo={row.get('comboId')} | course={row.get('courseId')} | "
                    f"title={row.get('title')} | themes={row.get('themes')}"
                ),
                entity_id=f"{combo_id}:{row.get('courseId')}",
                segment=segment,
            )
            for row in rows
        ]

    def _intersection(
        self,
        driver: Driver,
        entities: ResolvedEntities,
        *,
        segment: Segment,
    ) -> list[KnowledgeChunk]:
        if entities.intersection_pair is None:
            return []
        course_a, course_b = entities.intersection_pair
        rows = self._run(
            driver,
            """
            MATCH (c1:Course {id: $courseA})-[:COVERS]->(t:Theme)<-[:COVERS]-(c2:Course {id: $courseB})
            RETURN t.id AS themeId, t.name AS themeName
            ORDER BY t.id
            """,
            {"courseA": course_a, "courseB": course_b},
        )
        if not rows:
            return [
                _format_graph_chunk(
                    text=(
                        f"[graph] intersection | courseA={course_a} | courseB={course_b} | "
                        "sharedThemes=[]"
                    ),
                    entity_id=f"intersection:{course_a}:{course_b}",
                    segment=segment,
                ),
            ]
        themes = [str(row.get("themeId")) for row in rows]
        names = [str(row.get("themeName")) for row in rows]
        return [
            _format_graph_chunk(
                text=(
                    f"[graph] intersection | courseA={course_a} | courseB={course_b} | "
                    f"sharedThemes={themes} | names={names}"
                ),
                entity_id=f"intersection:{course_a}:{course_b}",
                segment=segment,
            ),
        ]

    def _theme_routing(
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
            OPTIONAL MATCH (t)-[:REQUIRES*1..3]->(prereq:Theme)
            RETURN c.id AS courseId,
                   c.title AS title,
                   t.id AS themeId,
                   collect(DISTINCT prereq.id) AS themePrereqs
            ORDER BY c.id
            """,
            {"themeId": theme_id},
        )
        chunks: list[KnowledgeChunk] = []
        for row in rows:
            chunks.append(
                _format_graph_chunk(
                    text=(
                        f"[graph] theme={row.get('themeId')} | course={row.get('courseId')} | "
                        f"title={row.get('title')} | themePrereqs={row.get('themePrereqs')}"
                    ),
                    entity_id=f"{theme_id}:{row.get('courseId')}",
                    segment=segment,
                ),
            )
        return chunks

    def _anchor_from_vector(
        self,
        query: str,
        *,
        segment: Segment,
        top_k: int,
    ) -> list[KnowledgeChunk]:
        try:
            vector_hits = self._vector.search(query, segment, top_k=min(top_k, 5))
        except Exception:  # noqa: BLE001
            return []
        driver = self._driver_or_cached()
        chunks: list[KnowledgeChunk] = []
        from mcp_server.retriever.graph_entities import (
            resolve_course_id_from_payload,  # noqa: PLC0415
        )

        for hit in vector_hits:
            course_id = resolve_course_id_from_payload(source=hit.get("source", ""))
            if course_id:
                chunks.extend(self._course_context(driver, course_id, segment=segment))
        return chunks
