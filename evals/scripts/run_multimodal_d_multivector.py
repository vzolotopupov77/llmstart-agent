"""Orchestrate method D: Jina multivector, retrieval eval, TEDS, D vs C/B report."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client import QdrantClient

from indexers.config import EVALS_ROOT, REPO_ROOT
from indexers.factory import load_multimodal_config, make_indexer
from indexers.jina_multivector.client import require_jina_key
from indexers.jina_multivector.factory import smoke_embed_image
from scripts.multimodal_models import load_multimodal_dataset
from scripts.multimodal_retrieval import JinaMultivectorEmbedder, run_retrieval_eval
from scripts.teds_score import score_teds
from scripts.teds_structure_extract import DEFAULT_OUT_DIR, run_structure_extract

logger = logging.getLogger(__name__)

CONFIG_PATH = EVALS_ROOT / "configs" / "multimodal-d-multivector.yaml"
SMOKE_IMAGE = REPO_ROOT / "data" / "multimodal-rag" / "slide-01.png"

C_REFERENCE: dict[str, dict[str, float]] = {
    "S1_text": {"recall_at_k": 1.000, "ndcg_at_5": 1.000},
    "S2_chart": {"recall_at_k": 1.000, "ndcg_at_5": 1.000},
    "S3_layout": {"recall_at_k": 0.900, "ndcg_at_5": 0.826},
    "S4_multi": {"recall_at_k": 0.833, "ndcg_at_5": 0.681},
    "S5_unanswerable": {"trap_in_topk": 0.833},
}

B_REFERENCE: dict[str, dict[str, dict[str, float]]] = {
    "nemotron": {
        "S1_text": {"recall_at_k": 0.857, "ndcg_at_5": 0.776},
        "S2_chart": {"recall_at_k": 1.000, "ndcg_at_5": 1.000},
        "S3_layout": {"recall_at_k": 0.700, "ndcg_at_5": 0.663},
        "S4_multi": {"recall_at_k": 1.000, "ndcg_at_5": 0.876},
        "S5_unanswerable": {"trap_in_topk": 0.833},
    },
    "gemini": {
        "S1_text": {"recall_at_k": 0.714, "ndcg_at_5": 0.714},
        "S2_chart": {"recall_at_k": 1.000, "ndcg_at_5": 1.000},
        "S3_layout": {"recall_at_k": 0.800, "ndcg_at_5": 0.800},
        "S4_multi": {"recall_at_k": 1.000, "ndcg_at_5": 0.819},
        "S5_unanswerable": {"trap_in_topk": 1.000},
    },
}

COST_REFERENCE = {
    "C": {"build_time_s": 207.37, "index_size_mb": 0.516, "est_cost_usd": 0.0},
    "B_nemotron": {"build_time_s": 606.29, "index_size_mb": 0.193, "est_cost_usd": 0.006022},
    "B_gemini": {"build_time_s": 398.53, "index_size_mb": 0.193, "est_cost_usd": 0.021415},
    "A_tesseract": {"build_time_s": 73.05, "index_size_mb": None, "est_cost_usd": 0.0},
}


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _best_b_metrics(segment: str) -> tuple[float | None, float | None]:
    n = B_REFERENCE["nemotron"].get(segment, {})
    g = B_REFERENCE["gemini"].get(segment, {})
    recall = max(n.get("recall_at_k", 0.0), g.get("recall_at_k", 0.0))
    ndcg = max(n.get("ndcg_at_5", 0.0), g.get("ndcg_at_5", 0.0))
    if "recall_at_k" not in n and "recall_at_k" not in g:
        recall = None
    if "ndcg_at_5" not in n and "ndcg_at_5" not in g:
        ndcg = None
    return recall, ndcg


def _cost_multiplier(value: float | None, baseline: float | None) -> str:
    if value is None or baseline is None or baseline == 0:
        return "—"
    return f"{value / baseline:.2f}×"


def write_report(
    path: Path,
    *,
    smoke_num_vectors: int,
    smoke_token_dim: int,
    run_payload: dict[str, object],
    teds_rows: list[tuple[int, str, float]],
    timestamp: str,
) -> None:
    aggregates = run_payload["aggregates"]
    model_id = str(run_payload["embed_model"])
    build_time_s = float(run_payload["build_time_s"])
    est_cost_usd = float(run_payload["est_cost_usd"])
    index_size_mb = run_payload.get("index_size_mb")
    total_tokens = run_payload.get("total_tokens")

    lines = [
        "# Multimodal RAG — method D Multivector (Task 07)",
        "",
        f"> **Дата:** {timestamp[:10]}",
        "> **Спринт:** "
        "[sprint-10-multimodal-rag](../../docs/sprints/sprint-10-multimodal-rag/README.md)",
        "> **Metric map:** "
        "[metric_map.md](../../docs/sprints/sprint-10-multimodal-rag/metric_map.md)",
        "",
        "---",
        "",
        "## Конфигурация",
        "",
        "| Параметр | Значение |",
        "|---|---|",
        f"| model_id | `{model_id}` |",
        f"| token_dim | {smoke_token_dim} |",
        f"| smoke vectors (slide-01) | {smoke_num_vectors} |",
        f"| d_max_side | {run_payload.get('d_max_side', '—')} |",
        f"| collection | `{run_payload['collection']}` |",
        f"| corpus_dir | `{run_payload['corpus_dir']}` |",
        "",
        "Index: PNG → Jina v4 multivector (`return_multivector=true`) → Qdrant MAX_SIM.",
        "Query: Jina v4 text multivector (`task=retrieval.query`).",
        "",
        "## Retrieval D по сегментам",
        "",
        "| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for segment, agg in sorted(aggregates.items()):
        set_r = agg.get("set_recall_at_k")
        trap = agg.get("trap_slide_in_topk")
        set_cell = f"{set_r:.3f}" if set_r is not None else "—"
        trap_cell = f"{trap:.3f}" if trap is not None else "—"
        lines.append(
            f"| {segment} | {int(agg['n'])} | {agg['recall_at_k']:.3f} | "
            f"{agg['ndcg_at_5']:.3f} | {agg['mrr']:.3f} | "
            f"{set_cell} | {trap_cell} |",
        )

    lines.extend(
        [
            "",
            "## D vs C по сегментам",
            "",
            "C reference: [multimodal-c-unified.md](multimodal-c-unified.md) "
            "(Task 06, 2026-07-11).",
            "",
            "| Сегмент | D Recall@5 | D nDCG@5 | C R/nDCG | Δ Recall (D−C) |",
            "|---|---:|---:|---|---:|",
        ],
    )
    for segment, agg in sorted(aggregates.items()):
        d_r = float(agg["recall_at_k"])
        d_n = float(agg["ndcg_at_5"])
        c = C_REFERENCE.get(segment, {})
        c_r = c.get("recall_at_k")
        c_n = c.get("ndcg_at_5")
        if c_r is not None and c_n is not None:
            c_cell = f"{c_r:.3f}/{c_n:.3f}"
            delta = f"{d_r - float(c_r):+.3f}"
        else:
            c_cell = "—"
            delta = "—"
        lines.append(f"| {segment} | {d_r:.3f} | {d_n:.3f} | {c_cell} | {delta} |")

    lines.extend(
        [
            "",
            "## D vs best B по сегментам",
            "",
            "B reference: [multimodal-b-caption.md](multimodal-b-caption.md) "
            "(Task 05, 2026-07-10).",
            "",
            "| Сегмент | D Recall@5 | D nDCG@5 | best B R/nDCG | Δ Recall (D−best B) |",
            "|---|---:|---:|---|---:|",
        ],
    )
    for segment, agg in sorted(aggregates.items()):
        d_r = float(agg["recall_at_k"])
        d_n = float(agg["ndcg_at_5"])
        best_r, best_n = _best_b_metrics(segment)
        if best_r is not None:
            best_cell = f"{best_r:.3f}/{best_n:.3f}" if best_n is not None else f"{best_r:.3f}/—"
            delta = f"{d_r - best_r:+.3f}"
        else:
            best_cell = "—"
            delta = "—"
        lines.append(f"| {segment} | {d_r:.3f} | {d_n:.3f} | {best_cell} | {delta} |")

    size_cell = f"{float(index_size_mb):.3f}" if isinstance(index_size_mb, (int, float)) else "—"
    embed_t = run_payload.get("embed_time_s")
    upsert_t = run_payload.get("upsert_time_s")
    embed_cell = f"{float(embed_t):.2f}" if embed_t is not None else "—"
    upsert_cell = f"{float(upsert_t):.2f}" if upsert_t is not None else "—"
    tokens_cell = str(int(total_tokens)) if total_tokens is not None else "—"

    size_float = float(index_size_mb) if index_size_mb else None
    mult_build_c = _cost_multiplier(build_time_s, COST_REFERENCE["C"]["build_time_s"])
    mult_build_b = _cost_multiplier(build_time_s, COST_REFERENCE["B_gemini"]["build_time_s"])
    mult_build_a = _cost_multiplier(build_time_s, COST_REFERENCE["A_tesseract"]["build_time_s"])
    mult_size_c = _cost_multiplier(size_float, COST_REFERENCE["C"]["index_size_mb"])
    mult_size_b = _cost_multiplier(size_float, COST_REFERENCE["B_gemini"]["index_size_mb"])
    mult_cost_c = _cost_multiplier(
        est_cost_usd if est_cost_usd else None,
        COST_REFERENCE["C"]["est_cost_usd"] or None,
    )
    mult_cost_b = _cost_multiplier(
        est_cost_usd if est_cost_usd else None,
        COST_REFERENCE["B_gemini"]["est_cost_usd"],
    )

    lines.extend(
        [
            "",
            "## Время и стоимость",
            "",
            "| Метод | build_time_s | embed_time_s | upsert_time_s | index_size_mb | "
            "total_tokens | api_calls | est_cost_usd |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            f"| D (multivector) | {build_time_s:.2f} | {embed_cell} | {upsert_cell} | "
            f"{size_cell} | {tokens_cell} | {int(run_payload.get('api_calls', 0))} | "
            f"{est_cost_usd:.6f} |",
            f"| C (unified) | {COST_REFERENCE['C']['build_time_s']:.2f} | — | — | "
            f"{COST_REFERENCE['C']['index_size_mb']:.3f} | — | 66 | "
            f"{COST_REFERENCE['C']['est_cost_usd']:.6f} |",
            f"| B gemini | {COST_REFERENCE['B_gemini']['build_time_s']:.2f} | — | — | "
            f"{COST_REFERENCE['B_gemini']['index_size_mb']:.3f} | — | 66 | "
            f"{COST_REFERENCE['B_gemini']['est_cost_usd']:.6f} |",
            f"| A tesseract | {COST_REFERENCE['A_tesseract']['build_time_s']:.2f} | — | — | "
            f"— | — | 66 | {COST_REFERENCE['A_tesseract']['est_cost_usd']:.6f} |",
            "",
            "### Мультипликаторы D относительно других методов",
            "",
            "| Метрика | vs C | vs B gemini | vs A tesseract |",
            "|---|---:|---:|---:|",
            f"| build_time_s | {mult_build_c} | {mult_build_b} | {mult_build_a} |",
            f"| index_size_mb | {mult_size_c} | {mult_size_b} | — |",
            f"| est_cost_usd | {mult_cost_c} | {mult_cost_b} | — |",
            "",
            "## TEDS (ingestion-quality, slides 10/11)",
            "",
            "**Формула:** TEDS = 1 − TED(tree_ref, tree_hyp) / max(|tree_ref|, |tree_hyp|).",
            "**Reference:** `evals/datasets/multimodal/teds-golden/v001_2026-07-11.json` "
            "(ручная HTML).",
            f"**Hypothesis:** VLM structure → `{_rel(DEFAULT_OUT_DIR)}/slide-NN.html`.",
            "",
            "| slide | segment | TEDS |",
            "|---:|---|---:|",
        ],
    )
    for slide_id, segment, teds in teds_rows:
        lines.append(f"| {slide_id} | {segment} | {teds:.3f} |")
    if teds_rows:
        mean_teds = sum(row[2] for row in teds_rows) / len(teds_rows)
        lines.append(f"| **mean** | S2_chart | **{mean_teds:.3f}** |")

    s2 = aggregates.get("S2_chart", {})
    s3 = aggregates.get("S3_layout", {})
    d_s2_r = float(s2.get("recall_at_k", 0.0))
    d_s3_r = float(s3.get("recall_at_k", 0.0))
    c_s2_r = C_REFERENCE["S2_chart"]["recall_at_k"]
    c_s3_r = C_REFERENCE["S3_layout"]["recall_at_k"]
    best_s2_r, _ = _best_b_metrics("S2_chart")
    best_s3_r, _ = _best_b_metrics("S3_layout")

    hypothesis_s2 = d_s2_r > max(c_s2_r, best_s2_r or 0.0)
    hypothesis_s3 = d_s3_r > max(c_s3_r, best_s3_r or 0.0)
    verdict_parts = []
    if hypothesis_s2:
        verdict_parts.append("S2 прирост")
    else:
        verdict_parts.append("S2 без прироста")
    if hypothesis_s3:
        verdict_parts.append("S3 прирост")
    else:
        verdict_parts.append("S3 без прироста")

    lines.extend(
        [
            "",
            "## Гипотеза multivector на S2/S3",
            "",
            "Гипотеза: late-interaction multivector (Jina v4) даёт прирост на chart/layout "
            "(S2/S3) относительно C и B, но цена index_size_mb / build_time_s / $ — "
            "максимальная.",
            "",
            f"**Вердикт: {', '.join(verdict_parts)}.**",
            "",
            f"- D S2_chart: Recall@5={d_s2_r:.3f} (C={c_s2_r:.3f}, best B={best_s2_r:.3f})",
            f"- D S3_layout: Recall@5={d_s3_r:.3f} (C={c_s3_r:.3f}, best B={best_s3_r:.3f})",
            f"- D index_size_mb={size_cell} vs C={COST_REFERENCE['C']['index_size_mb']:.3f}",
            f"- D build_time_s={build_time_s:.2f} vs C={COST_REFERENCE['C']['build_time_s']:.2f}",
            f"- D est_cost_usd={est_cost_usd:.6f}",
            "",
            "## Вывод",
            "",
        ],
    )

    if hypothesis_s2 or hypothesis_s3:
        lines.append(
            "Multivector **показывает сегментный прирост** на S2 и/или S3; сравнить цену "
            "хранения и индексации с C/B в таблице мультипликаторов выше."
        )
    else:
        lines.append(
            "Multivector **не обогнал** C/B на S2/S3 при существенно большем `index_size_mb` — "
            "для этого корпуса цена multivector не оправдана retrieval-метриками."
        )

    lines.extend(
        [
            "",
            "Решение по сегментам, не macro-average. Сравнение с C: "
            "[multimodal-c-unified.md](multimodal-c-unified.md).",
            "",
        ],
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _prior_index_stats(config_id: str) -> dict[str, object] | None:
    """Load index metrics from latest run JSON with non-zero build_time_s."""
    runs_dir = REPO_ROOT / "evals" / "reports" / "runs"
    for path in sorted(runs_dir.glob("multimodal-d-multivector-*.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("config_id") != config_id:
            continue
        if float(data.get("build_time_s", 0.0)) > 0:
            return data
    return None


# Fallback from successful index run 2026-07-11 (when --skip-index before prior JSON exists)
_INDEX_RUN_FALLBACK: dict[str, object] = {
    "build_time_s": 631.11,
    "embed_time_s": 487.14,
    "upsert_time_s": 143.96,
    "est_cost_usd": 0.025641,
    "api_calls": 66,
    "index_size_mb": 24.202,
    "total_tokens": 49566,
    "indexed_slides": 66,
}


def run_eval(
    *, skip_index: bool, skip_teds: bool
) -> tuple[dict[str, object], list[tuple[int, str, float]]]:
    cfg = load_multimodal_config(CONFIG_PATH)
    model_id = cfg.embedding_model
    indexer = make_indexer(cfg)

    build_time_s = 0.0
    est_cost_usd = 0.0
    index_size_mb = None
    indexed_slides = 0
    api_calls = 0
    embed_time_s = None
    upsert_time_s = None
    total_tokens = None

    if not skip_index:
        index_cost = indexer.build_index(cfg.corpus_dir)
        build_time_s = index_cost.build_time_s
        est_cost_usd = index_cost.est_cost_usd
        index_size_mb = index_cost.index_size_mb
        indexed_slides = getattr(indexer, "indexed_slides", 0)
        api_calls = index_cost.api_calls
        embed_time_s = getattr(indexer, "embed_time_s", None)
        upsert_time_s = getattr(indexer, "upsert_time_s", None)
        total_tokens = getattr(indexer, "total_tokens", None)
        logger.info(
            "Indexed D: %d slides in %.2fs ($%.6f, %.3f MB)",
            indexed_slides,
            build_time_s,
            est_cost_usd,
            float(index_size_mb or 0.0),
        )
    else:
        prior = _prior_index_stats(cfg.config_id) or _INDEX_RUN_FALLBACK
        build_time_s = float(prior.get("build_time_s", 0.0))
        est_cost_usd = float(prior.get("est_cost_usd", 0.0))
        index_size_mb = prior.get("index_size_mb")
        indexed_slides = int(prior.get("indexed_slides", 0))
        api_calls = int(prior.get("api_calls", 0))
        embed_time_s = prior.get("embed_time_s")
        upsert_time_s = prior.get("upsert_time_s")
        total_tokens = prior.get("total_tokens")
        logger.info(
            "Using prior index stats: %d slides, %.2fs, %.3f MB",
            indexed_slides,
            build_time_s,
            float(index_size_mb or 0.0),
        )

    embedder = JinaMultivectorEmbedder(model_id, token_dim=cfg.embedding_dim)
    client = QdrantClient(url=cfg.qdrant_url)
    dataset = load_multimodal_dataset(cfg.dataset_path)
    item_rows, aggregates = run_retrieval_eval(cfg, dataset, embedder=embedder, client=client)

    teds_rows: list[tuple[int, str, float]] = []
    if not skip_teds:
        run_structure_extract(out_dir=DEFAULT_OUT_DIR)
        teds_report = score_teds(DEFAULT_OUT_DIR)
        teds_rows = [(s.slide_id, s.segment, s.teds) for s in teds_report.scores]

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_name = f"multimodal-d-multivector-{timestamp}.json"
    run_path = REPO_ROOT / "evals" / "reports" / "runs" / run_name
    run_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "config_id": cfg.config_id,
        "embed_model": model_id,
        "collection": cfg.collection,
        "corpus_dir": _rel(cfg.corpus_dir),
        "d_max_side": cfg.d_max_side,
        "build_time_s": build_time_s,
        "embed_time_s": embed_time_s,
        "upsert_time_s": upsert_time_s,
        "est_cost_usd": est_cost_usd,
        "api_calls": api_calls,
        "index_size_mb": index_size_mb,
        "total_tokens": total_tokens,
        "indexed_slides": indexed_slides,
        "aggregates": aggregates,
        "teds": [{"slide_id": s, "segment": seg, "teds": t} for s, seg, t in teds_rows],
        "items": item_rows,
    }
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Run JSON: %s", run_path)
    return payload, teds_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Method D Jina multivector eval")
    parser.add_argument("--skip-index", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--skip-teds", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = load_multimodal_config(CONFIG_PATH)
    model_id = cfg.embedding_model
    max_side = cfg.d_max_side or 1024

    require_jina_key()
    logger.info("JINA_API_KEY present")

    smoke_num_vectors = 0
    smoke_token_dim = cfg.embedding_dim
    if not args.skip_smoke and SMOKE_IMAGE.exists():
        logger.info("Smoke Jina multivector on slide-01")
        result = smoke_embed_image(
            model_id,
            SMOKE_IMAGE,
            max_side=max_side,
            token_dim=cfg.embedding_dim,
        )
        smoke_num_vectors = result.num_vectors
        if result.vectors and len(result.vectors[0]) != cfg.embedding_dim:
            actual = len(result.vectors[0])
            msg = (
                f"Config embedding_dim={cfg.embedding_dim} but smoke returned "
                f"token_dim={actual}; update multimodal-d-multivector.yaml"
            )
            raise RuntimeError(msg)
        smoke_token_dim = len(result.vectors[0]) if result.vectors else cfg.embedding_dim
        logger.info(
            "Smoke OK: %d vectors x dim=%d, $%.6f, %.2fs",
            smoke_num_vectors,
            smoke_token_dim,
            result.est_cost_usd,
            result.latency_s,
        )

    run_payload, teds_rows = run_eval(skip_index=args.skip_index, skip_teds=args.skip_teds)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_path = REPO_ROOT / "evals" / "reports" / "multimodal-d-multivector.md"
    write_report(
        report_path,
        smoke_num_vectors=smoke_num_vectors,
        smoke_token_dim=smoke_token_dim,
        run_payload=run_payload,
        teds_rows=teds_rows,
        timestamp=timestamp,
    )
    logger.info("Report: %s", report_path)


if __name__ == "__main__":
    main()
