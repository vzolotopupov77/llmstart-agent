"""Auto-extract Theme/Course relationships from program markdown via SimpleKGPipeline.

Usage:
    cd mcp_server && uv run python ../scripts/graph_indexer.py

Requires: neo4j-graphrag, OPENAI_API_KEY, running Neo4j with seed loaded.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.exceptions import LLMGenerationError
from neo4j_graphrag.experimental.components.schema import (
    GraphSchema,
    NodeType,
    PropertyType,
    RelationshipType,
)
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import OpenAILLM

# Allow running as script from mcp_server venv
sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_common import (
    FILE_TO_COURSE,
    PROGRAMS_DIR,
    REPO_ROOT,
    SEED_COURSE_IDS,
    SEED_THEME_REQUIRES,
    THEME_ALIAS_PATCHES,
    GraphSettings,
    build_theme_alias_index,
    exact_theme_id_match,
    load_seed_themes,
    resolve_theme_id,
    slugify,
)

EXTRACTION_STATS_PATH = REPO_ROOT / "data" / "graph" / "extraction-stats.json"

logger = logging.getLogger(__name__)

# LLM extracts Theme + REQUIRES only. Course nodes come from seed; COVERS is post-processed
# via FILE_TO_COURSE (avoids constraint conflicts on course_id_unique).
ALLOWED_NODE_LABELS = ("Theme",)
ALLOWED_REL_TYPES = ("REQUIRES", "COVERS")
# COVERS: seed Course -> Theme, linked in _link_covers_from_documents (not by LLM)


def _build_extraction_schema() -> GraphSchema:
    """Strict schema: Theme nodes and REQUIRES edges only."""
    return GraphSchema(
        node_types=[
            NodeType(
                label="Theme",
                description="A technical topic covered by courses",
                properties=[
                    PropertyType(name="id", type="STRING"),
                    PropertyType(name="name", type="STRING"),
                ],
            ),
        ],
        relationship_types=[
            RelationshipType(
                label="REQUIRES",
                description="Theme requires prerequisite theme (Theme -> Theme)",
            ),
        ],
        patterns=[
            ("Theme", "REQUIRES", "Theme"),
        ],
    )


def _build_pipeline(settings: GraphSettings, driver: GraphDatabase) -> SimpleKGPipeline:  # type: ignore[type-arg]
    openai_kwargs = {
        "api_key": settings.openai_api_key,
        "base_url": settings.openai_base_url,
    }
    llm = OpenAILLM(
        model_name=settings.extract_model,
        model_params={"temperature": 0},
        **openai_kwargs,
    )
    embedder = OpenAIEmbeddings(model=settings.embedding_model, **openai_kwargs)
    return SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        schema=_build_extraction_schema(),
        from_file=True,
        on_error="IGNORE",
        perform_entity_resolution=False,
        text_splitter=FixedSizeSplitter(chunk_size=512, chunk_overlap=64, approximate=True),
        neo4j_database="neo4j",
    )


async def _run_extraction(
    pipeline: SimpleKGPipeline,
    files: list[Path],
) -> list[str]:
    """Run pipeline per file; continue on LLM/Neo4j errors. Returns failed filenames."""
    failed: list[str] = []
    for path in files:
        course_id = FILE_TO_COURSE.get(path.name)
        meta = {
            "source_file": path.name,
            "course_id": course_id or "",
            "source": "auto",
        }
        print(f"  extracting: {path.name} -> course={course_id or 'n/a'}")
        try:
            await pipeline.run_async(file_path=str(path), document_metadata=meta)
        except (LLMGenerationError, Neo4jError, OSError) as exc:
            print(f"  WARN: skip {path.name}: {exc}", file=sys.stderr)
            failed.append(path.name)
    return failed


def _verify_openrouter(settings: GraphSettings) -> bool:
    """Fail fast when OpenRouter credentials are invalid."""
    try:
        import openai
    except ImportError:
        print("ERROR: openai package missing (neo4j-graphrag[openai])", file=sys.stderr)
        return False

    client = openai.OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    try:
        client.embeddings.create(input="ping", model=settings.embedding_model)
        client.chat.completions.create(
            model=settings.extract_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
    except openai.AuthenticationError as exc:
        print(
            f"ERROR: OpenRouter auth failed (check OPENAI_API_KEY / OPENAI_BASE_URL): {exc}",
            file=sys.stderr,
        )
        return False
    except openai.APIError as exc:
        print(f"ERROR: OpenRouter API check failed: {exc}", file=sys.stderr)
        return False
    return True


def _theme_id_str(node_id: object | None, canonical_ids: frozenset[str]) -> str | None:
    if node_id is None:
        return None
    if isinstance(node_id, list):
        for item in node_id:
            sid = str(item).strip()
            if sid in canonical_ids:
                return sid
        return str(node_id[0]).strip() if node_id else None
    return str(node_id).strip()


def _finalize_catalog(
    driver: GraphDatabase,  # type: ignore[type-arg]
    *,
    canonical_ids: frozenset[str],
    strict: bool,
) -> None:
    """Fix list-typed properties; merge or drop invalid themes."""
    driver.execute_query(
        """
        MATCH (t:Theme)
        WHERE t.name IS NOT NULL AND NOT t.name IS :: STRING
        SET t.name = t.name[0]
        """,
        database_="neo4j",
    )

    bad_id_records, _, _ = driver.execute_query(
        """
        MATCH (t:Theme)
        WHERE t.id IS NOT NULL AND NOT t.id IS :: STRING
        RETURN elementId(t) AS eid, t.id AS rawId, t.name AS name
        """,
        database_="neo4j",
    )
    for rec in bad_id_records:
        eid = str(rec["eid"])
        fixed_id = _theme_id_str(rec["rawId"], canonical_ids)
        name_str = _theme_name_str(rec["name"])
        if fixed_id and fixed_id in canonical_ids:
            _merge_theme_into_canonical(
                driver, dup_element_id=eid, canon_id=fixed_id, dup_name=name_str
            )
        else:
            _delete_theme(driver, eid)

    driver.execute_query(
        "MATCH (t:Theme) WHERE t.id IS NULL DETACH DELETE t",
        database_="neo4j",
    )
    if strict:
        driver.execute_query(
            """
            MATCH (t:Theme)
            WHERE NOT t.id IN $ids
            DETACH DELETE t
            """,
            ids=list(canonical_ids),
            database_="neo4j",
        )
    driver.execute_query(
        """
        MATCH (t:Theme)
        WHERE NOT (t)--()
        DETACH DELETE t
        """,
        database_="neo4j",
    )


def _theme_name_str(name: object | None) -> str | None:
    if name is None:
        return None
    if isinstance(name, list):
        return str(name[0]) if name else None
    return str(name)


def _cleanup_previous_extraction(driver: GraphDatabase) -> None:  # type: ignore[type-arg]
    """Remove lexical-layer nodes and spurious courses from prior runs."""
    driver.execute_query(
        """
        MATCH (c:Course)
        WHERE c.id IS NULL OR NOT c.id IN $seedIds
        DETACH DELETE c
        """,
        seedIds=list(SEED_COURSE_IDS),
        database_="neo4j",
    )
    driver.execute_query("MATCH (d:Document) DETACH DELETE d", database_="neo4j")
    driver.execute_query("MATCH (ch:Chunk) DETACH DELETE ch", database_="neo4j")
    # Orphan __KGBuilder__ stubs left by failed pipeline writes
    driver.execute_query(
        """
        MATCH (n:__KGBuilder__)
        WHERE NOT n:Theme AND NOT n:Course
        DETACH DELETE n
        """,
        database_="neo4j",
    )


def _merge_theme_into_canonical(
    driver: GraphDatabase,  # type: ignore[type-arg]
    *,
    dup_element_id: str,
    canon_id: str,
    dup_name: str | None,
) -> None:
    """Merge dup Theme into canonical seed node; keep canonical properties (discard dup props)."""
    driver.execute_query(
        """
        MATCH (dup:Theme) WHERE elementId(dup) = $dupEid
        MATCH (canon:Theme {id: $canonId})
        WHERE elementId(dup) <> elementId(canon)
        CALL apoc.refactor.mergeNodes([canon, dup], {
            properties: 'discard',
            mergeRels: true
        }) YIELD node
        SET node.source = 'seed',
            node.aliases = apoc.coll.toSet(
                coalesce(node.aliases, [])
                + CASE WHEN $dupName IS NOT NULL AND $dupName <> node.name
                       THEN [$dupName] ELSE [] END
            )
        """,
        dupEid=dup_element_id,
        canonId=canon_id,
        dupName=dup_name,
        database_="neo4j",
    )


def _mark_auto_theme(
    driver: GraphDatabase,  # type: ignore[type-arg]
    *,
    element_id: str,
    theme_id: str,
    name: str,
) -> None:
    driver.execute_query(
        """
        MATCH (t:Theme) WHERE elementId(t) = $eid
        SET t.id = $id, t.name = $name, t.source = 'auto',
            t.aliases = coalesce(t.aliases, [])
        """,
        eid=element_id,
        id=theme_id,
        name=name,
        database_="neo4j",
    )


def _delete_theme(driver: GraphDatabase, element_id: str) -> None:  # type: ignore[type-arg]
    driver.execute_query(
        "MATCH (t:Theme) WHERE elementId(t) = $eid DETACH DELETE t",
        eid=element_id,
        database_="neo4j",
    )


def _resolve_auto_themes(
    driver: GraphDatabase,  # type: ignore[type-arg]
    *,
    alias_index: dict[str, str],
    canonical_ids: frozenset[str],
    strict: bool,
) -> dict[str, int]:
    """Entity resolution: merge auto themes into canonical seed nodes."""
    stats: dict[str, int | set[str]] = {
        "merged": 0,
        "created": 0,
        "dropped": 0,
        "skipped": 0,
        "auto_raw": 0,
        "exact_seed_ids": set(),
        "semantic_seed_ids": set(),
    }

    records, _, _ = driver.execute_query(
        """
        MATCH (t:Theme)
        WHERE t:__Entity__ OR coalesce(t.source, 'auto') <> 'seed'
        RETURN elementId(t) AS eid, t.id AS id, t.name AS name, t.source AS source
        """,
        database_="neo4j",
    )

    for rec in records:
        eid = str(rec["eid"])
        name_str = _theme_name_str(rec["name"])
        node_id_str = _theme_id_str(rec["id"], canonical_ids)
        source = rec.get("source")

        if source == "seed" and node_id_str in canonical_ids:
            stats["skipped"] += 1
            continue

        stats["auto_raw"] = int(stats["auto_raw"]) + 1
        exact = exact_theme_id_match(
            name=name_str, node_id=node_id_str, canonical_ids=canonical_ids
        )
        if exact:
            cast_exact = stats["exact_seed_ids"]
            assert isinstance(cast_exact, set)
            cast_exact.add(exact)

        canon = resolve_theme_id(
            name=name_str,
            node_id=node_id_str,
            alias_index=alias_index,
            canonical_ids=canonical_ids,
        )

        if canon and node_id_str == canon and source == "seed":
            stats["skipped"] += 1
            continue

        if canon:
            cast_sem = stats["semantic_seed_ids"]
            assert isinstance(cast_sem, set)
            cast_sem.add(canon)
            _merge_theme_into_canonical(
                driver, dup_element_id=eid, canon_id=canon, dup_name=name_str
            )
            stats["merged"] += 1
            print(f"    merge theme -> {canon}: {name_str or node_id_str}")
        elif strict:
            _delete_theme(driver, eid)
            stats["dropped"] += 1
            print(f"    drop (strict): {name_str or node_id_str}")
        else:
            new_id = node_id_str or slugify(name_str or "unknown")
            _mark_auto_theme(driver, element_id=eid, theme_id=new_id, name=name_str or new_id)
            stats["created"] += 1
            print(f"    keep auto: {new_id}")

    return stats


def _save_extraction_stats(
    stats: dict[str, int | set[str]],
    *,
    seed_count: int,
    all_seed_ids: frozenset[str],
) -> None:
    exact_ids = stats.get("exact_seed_ids", set())
    semantic_ids = stats.get("semantic_seed_ids", set())
    assert isinstance(exact_ids, set)
    assert isinstance(semantic_ids, set)
    auto_raw = int(stats.get("auto_raw", 0))
    payload = {
        "generated_at": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed_themes": seed_count,
        "auto_raw": auto_raw,
        "merged": int(stats.get("merged", 0)),
        "dropped": int(stats.get("dropped", 0)),
        "created": int(stats.get("created", 0)),
        "exact_seed_count": len(exact_ids),
        "semantic_seed_count": len(semantic_ids),
        "exact_seed_ids": sorted(exact_ids),
        "semantic_seed_ids": sorted(semantic_ids),
        "unmatched_seed_ids": sorted(all_seed_ids - semantic_ids),
        "exact_recall_pct": round(100 * len(exact_ids) / seed_count, 1) if seed_count else 0.0,
        "semantic_recall_pct": round(100 * len(semantic_ids) / seed_count, 1)
        if seed_count
        else 0.0,
        "proliferation_factor": round(auto_raw / seed_count, 1) if seed_count else 0.0,
    }
    EXTRACTION_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXTRACTION_STATS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _remove_spurious_courses(driver: GraphDatabase) -> int:  # type: ignore[type-arg]
    """Delete Course nodes outside the 4 seed courses (incl. null id)."""
    summary = driver.execute_query(
        """
        MATCH (c:Course)
        WHERE c.id IS NULL OR NOT c.id IN $seedIds
        DETACH DELETE c
        RETURN count(*) AS deleted
        """,
        seedIds=list(SEED_COURSE_IDS),
        database_="neo4j",
    ).summary
    return summary.counters.nodes_deleted


def _link_covers_from_documents(driver: GraphDatabase) -> int:  # type: ignore[type-arg]
    """Create COVERS edges from seed Course to themes mentioned in each document."""
    linked = 0
    for filename, course_id in FILE_TO_COURSE.items():
        if not course_id:
            continue
        summary = driver.execute_query(
            """
            MATCH (doc:Document)
            WHERE doc.path ENDS WITH $filename OR doc.fileName ENDS WITH $filename
            MATCH (c:Course {id: $courseId})
            MATCH (doc)-[:FROM_DOCUMENT]-(:Chunk)<-[:FROM_CHUNK]-(t:Theme)
            MERGE (c)-[r:COVERS]->(t)
            ON CREATE SET r.source = 'auto', r.depth = coalesce(r.depth, 'core')
            ON MATCH SET r.source = coalesce(r.source, 'auto')
            """,
            filename=filename,
            courseId=course_id,
            database_="neo4j",
        ).summary
        linked += summary.counters.relationships_created
    return linked


def _cleanup_lexical_layer(driver: GraphDatabase) -> None:  # type: ignore[type-arg]
    """Remove Document/Chunk nodes and pipeline labels after COVERS linking."""
    driver.execute_query("MATCH (d:Document) DETACH DELETE d", database_="neo4j")
    driver.execute_query("MATCH (ch:Chunk) DETACH DELETE ch", database_="neo4j")
    driver.execute_query(
        """
        MATCH (n:Theme) REMOVE n:__Entity__, n:__KGBuilder__
        WITH count(n) AS _
        MATCH (c:Course) REMOVE c:__Entity__, c:__KGBuilder__
        """,
        database_="neo4j",
    )


def _finalize_seed_requires(driver: GraphDatabase) -> dict[str, int]:  # type: ignore[type-arg]
    """Drop LLM REQUIRES (dupes, self-loops, noise); restore seed-only prerequisites."""
    summary = driver.execute_query(
        "MATCH (:Theme)-[r:REQUIRES]->(:Theme) DELETE r",
        database_="neo4j",
    ).summary
    deleted = summary.counters.relationships_deleted

    restored = 0
    for from_id, to_id in SEED_THEME_REQUIRES:
        driver.execute_query(
            """
            MATCH (a:Theme {id: $fromId}), (b:Theme {id: $toId})
            MERGE (a)-[r:REQUIRES]->(b)
            SET r.source = 'seed'
            """,
            fromId=from_id,
            toId=to_id,
            database_="neo4j",
        )
        restored += 1

    return {"requires_deleted": deleted, "requires_seed": restored}


def _dedupe_relationships(driver: GraphDatabase, rel_type: str) -> int:  # type: ignore[type-arg]
    """Keep one relationship per (start, end) pair; return deleted count."""
    _, summary, _ = driver.execute_query(
        f"""
        MATCH ()-[r:{rel_type}]->()
        WITH startNode(r) AS a, endNode(r) AS b, collect(r) AS rs
        WHERE size(rs) > 1
        UNWIND tail(rs) AS dup
        DELETE dup
        RETURN count(*) AS deleted
        """,
        database_="neo4j",
    )
    return int(summary.counters.relationships_deleted)


def _apply_theme_alias_patches(driver: GraphDatabase) -> int:  # type: ignore[type-arg]
    """Part D: enrich keep-themes with aliases from extraction review."""
    patched = 0
    for theme_id, extra_aliases in THEME_ALIAS_PATCHES.items():
        summary = driver.execute_query(
            """
            MATCH (t:Theme {id: $id})
            SET t.aliases = apoc.coll.toSet(coalesce(t.aliases, []) + $extra)
            RETURN size($extra) AS added
            """,
            id=theme_id,
            extra=list(extra_aliases),
            database_="neo4j",
        ).summary
        if summary.counters.properties_set:
            patched += 1
    return patched


def _verify_catalog_invariants(driver: GraphDatabase) -> dict[str, int]:  # type: ignore[type-arg]
    """Part D sanity checks after finalization."""
    rows, _, _ = driver.execute_query(
        """
        OPTIONAL MATCH (n) WHERE NOT (n)--()
        WITH count(n) AS orphans
        OPTIONAL MATCH ()-[r:REQUIRES]->()
        WITH orphans, count(r) AS requiresCnt
        OPTIONAL MATCH (a:Theme)-[r:REQUIRES]->(b:Theme) WHERE a.id = b.id
        WITH orphans, requiresCnt, count(r) AS requireLoops
        RETURN orphans, requiresCnt, requireLoops
        """,
        database_="neo4j",
    )
    row = dict(rows[0]) if rows else {}
    return {
        "orphans": int(row.get("orphans") or 0),
        "requires": int(row.get("requiresCnt") or 0),
        "require_loops": int(row.get("requireLoops") or 0),
    }


def run_indexer() -> int:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("neo4j_graphrag.experimental.components.kg_writer").setLevel(logging.WARNING)
    settings = GraphSettings()

    if not settings.neo4j_password:
        print("ERROR: NEO4J_PASSWORD is not set", file=sys.stderr)
        return 1
    if not settings.openai_api_key:
        print("ERROR: OPENAI_API_KEY is not set (required for SimpleKGPipeline)", file=sys.stderr)
        return 1
    if not _verify_openrouter(settings):
        return 1
    if not PROGRAMS_DIR.is_dir():
        print(f"ERROR: programs dir not found: {PROGRAMS_DIR}", file=sys.stderr)
        return 1

    files = sorted(p for p in PROGRAMS_DIR.glob("*.md") if p.name in FILE_TO_COURSE)
    if not files:
        print("ERROR: no program files to process", file=sys.stderr)
        return 1

    print(
        f"=== graph-extract (model={settings.extract_model}, strict={settings.graph_extract_strict}) ==="
    )
    print(f"Allowed nodes: {ALLOWED_NODE_LABELS}; rels: {ALLOWED_REL_TYPES}")

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        driver.verify_connectivity()
    except (Neo4jError, OSError) as exc:
        print(f"ERROR: Neo4j unavailable: {exc}", file=sys.stderr)
        driver.close()
        return 1

    seed_themes = load_seed_themes(driver)
    if not seed_themes:
        print("ERROR: no seed themes - run make graph-seed first", file=sys.stderr)
        driver.close()
        return 1

    alias_index, canonical_ids = build_theme_alias_index(seed_themes)

    print("\nPhase 0: cleanup prior extraction artifacts")
    _cleanup_previous_extraction(driver)

    pipeline = _build_pipeline(settings, driver)
    print(f"\nPhase 1: SimpleKGPipeline on {len(files)} files")
    failed_files = asyncio.run(_run_extraction(pipeline, files))
    if failed_files:
        print(
            f"  {len(failed_files)} file(s) skipped: {', '.join(failed_files)}",
            file=sys.stderr,
        )
    # Pipeline may leave spurious Course nodes even when on_error=IGNORE
    spurious = _remove_spurious_courses(driver)
    if spurious:
        print(f"  cleaned spurious courses after Phase 1: {spurious}")

    print("\nPhase 2: COVERS from Document-Chunk-Theme (before lexical cleanup)")
    covers_linked = _link_covers_from_documents(driver)
    print(f"  COVERS edges created: {covers_linked}")

    print("\nPhase 3: entity resolution (theme aliases -> canonical)")
    theme_stats = _resolve_auto_themes(
        driver,
        alias_index=alias_index,
        canonical_ids=canonical_ids,
        strict=settings.graph_extract_strict,
    )

    print("\nPhase 4: cleanup spurious Course nodes")
    deleted_courses = _remove_spurious_courses(driver)
    print(f"  deleted spurious courses: {deleted_courses}")

    print("\nPhase 5: remove lexical layer (Document/Chunk)")
    _cleanup_lexical_layer(driver)

    print("\nPhase 6: finalize REQUIRES (seed-only, drop LLM noise)")
    requires_stats = _finalize_seed_requires(driver)
    print(
        f"  REQUIRES: deleted {requires_stats['requires_deleted']}, "
        f"restored {requires_stats['requires_seed']} seed edges"
    )

    print("\nPhase 7: finalize catalog (fix types, drop non-seed in strict mode)")
    _finalize_catalog(
        driver,
        canonical_ids=canonical_ids,
        strict=settings.graph_extract_strict,
    )

    print("\nPhase 8: entity resolution finalize (dedupe COVERS, alias patches, invariants)")
    covers_deduped = _dedupe_relationships(driver, "COVERS")
    alias_patched = _apply_theme_alias_patches(driver)
    invariants = _verify_catalog_invariants(driver)
    print(f"  COVERS duplicates removed: {covers_deduped}")
    print(f"  alias patches applied:     {alias_patched}")
    print(
        f"  invariants: orphans={invariants['orphans']}, "
        f"REQUIRES={invariants['requires']}, loops={invariants['require_loops']}"
    )

    _save_extraction_stats(theme_stats, seed_count=len(seed_themes), all_seed_ids=canonical_ids)
    driver.close()

    print("\n=== extraction summary ===")
    print(f"  themes merged:  {theme_stats['merged']}")
    print(f"  themes kept:    {theme_stats['created']}")
    print(f"  themes dropped: {theme_stats['dropped']} (strict={settings.graph_extract_strict})")
    if failed_files:
        print(
            f"  files failed:   {len(failed_files)} (re-run after fixing OPENAI_API_KEY)",
            file=sys.stderr,
        )
        return 1
    print("graph-extract done.")
    return 0


def main() -> int:
    return run_indexer()


if __name__ == "__main__":
    raise SystemExit(main())
