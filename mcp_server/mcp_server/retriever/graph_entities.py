"""Heuristic entity resolution from user queries for graph retrieval."""

from __future__ import annotations

import re
from dataclasses import dataclass

COURSE_SLUGS: frozenset[str] = frozenset(
    {"vibe-coding", "fullstack-aidd", "agents", "deep-agents", "ai-agents-combo"},
)

COMBO_SLUGS: frozenset[str] = frozenset({"ai-agents-combo"})

COURSE_ALIASES: dict[str, str] = {
    "vibe-coding-intensive": "vibe-coding",
    "ai-coding-intensive-cursor": "vibe-coding",
    "fullstack-aidd": "fullstack-aidd",
    "fullstack aidd": "fullstack-aidd",
    "ai-driven-fullstack": "fullstack-aidd",
    "aidd-program": "fullstack-aidd",
    "agents": "agents",
    "ai-coding-agents-base": "agents",
    "deep-agents": "deep-agents",
    "deep agents": "deep-agents",
    "ai-agents-combo": "ai-agents-combo",
    "комбо": "ai-agents-combo",
    "иі-агенты": "ai-agents-combo",
    "ии-агенты": "ai-agents-combo",
}

THEME_KEYWORDS: dict[str, str] = {
    "mcp": "mcp",
    "model context protocol": "mcp",
    "graphrag": "graphrag",
    "graph rag": "graphrag",
    "rag": "rag-basic",
    "observability": "observability",
    "langfuse": "observability",
    "ci/cd": "ci-cd",
    "vector": "vector-db",
    "векторн": "vector-db",
}

SOURCE_TO_COURSE: dict[str, str] = {
    "ai-coding-intensive-cursor.md": "vibe-coding",
    "ai-driven-fullstack.md": "fullstack-aidd",
    "aidd-program.md": "fullstack-aidd",
    "ai-coding-agents-base.md": "agents",
    "deep-agents-advanced.md": "deep-agents",
    "ai-agents-combo.md": "ai-agents-combo",
}


@dataclass(frozen=True)
class ResolvedEntities:
    """Entities extracted from a natural-language query."""

    course_ids: tuple[str, ...]
    combo_ids: tuple[str, ...]
    theme_ids: tuple[str, ...]
    intersection_pair: tuple[str, str] | None


def _find_slug_in_text(text: str, slug: str) -> bool:
    spaced = slug.replace("-", " ")
    if spaced in text:
        return True
    return re.search(rf"(?<![a-z0-9-]){re.escape(slug)}(?![a-z0-9-])", text) is not None


def _ordered_course_hits(lowered: str) -> list[str]:
    """Return canonical course/combo ids in query order; longer slugs win overlaps."""
    hits: list[tuple[int, str]] = []
    seen: set[str] = set()

    for alias, canonical in sorted(
        COURSE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True
    ):
        index = lowered.find(alias)
        if index >= 0 and canonical not in seen:
            hits.append((index, canonical))
            seen.add(canonical)

    for slug in sorted(COURSE_SLUGS, key=len, reverse=True):
        if slug in seen:
            continue
        index = lowered.find(slug)
        if index < 0 and not _find_slug_in_text(lowered, slug):
            continue
        if index < 0:
            index = lowered.find(slug.replace("-", " "))
        hits.append((index, slug))
        seen.add(slug)

    hits.sort(key=lambda item: item[0])
    ordered: list[str] = []
    for _, canonical in hits:
        if canonical not in ordered:
            ordered.append(canonical)
    return ordered


def resolve_course_id_from_payload(*, source: str, relative_path: str = "") -> str | None:
    """Map Qdrant chunk metadata to canonical Course.id."""
    if source in SOURCE_TO_COURSE:
        return SOURCE_TO_COURSE[source]
    path_key = relative_path.rsplit("/", maxsplit=1)[-1] if relative_path else source
    return SOURCE_TO_COURSE.get(path_key)


def extract_entities(query: str) -> ResolvedEntities:
    """Resolve course/combo/theme slugs and optional two-course intersection."""
    lowered = query.lower()
    found_courses = _ordered_course_hits(lowered)
    is_prereq = "перед" in lowered or "нужно пройти" in lowered

    combo_ids = tuple(dict.fromkeys(cid for cid in found_courses if cid in COMBO_SLUGS))
    course_ids = tuple(dict.fromkeys(cid for cid in found_courses if cid not in COMBO_SLUGS))

    theme_ids: list[str] = []
    for keyword, theme_id in THEME_KEYWORDS.items():
        if keyword in lowered and theme_id not in theme_ids:
            theme_ids.append(theme_id)

    intersection_pair: tuple[str, str] | None = None
    if (len(course_ids) >= 2 and not is_prereq) or (
        "общ" in lowered and "тем" in lowered and len(course_ids) >= 2
    ):
        intersection_pair = (course_ids[0], course_ids[1])

    return ResolvedEntities(
        course_ids=course_ids,
        combo_ids=combo_ids,
        theme_ids=tuple(theme_ids),
        intersection_pair=intersection_pair,
    )
