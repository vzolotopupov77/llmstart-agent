"""Orchestrate method C: VL image embed, retrieval eval, C vs B report."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client import QdrantClient

from indexers.config import EVALS_ROOT, REPO_ROOT
from indexers.factory import load_multimodal_config, make_indexer
from indexers.vl_embed.factory import preflight_model, smoke_embed
from scripts.multimodal_models import load_multimodal_dataset
from scripts.multimodal_retrieval import VLEmbedder, run_retrieval_eval

logger = logging.getLogger(__name__)

CONFIG_PATH = EVALS_ROOT / "configs" / "multimodal-c-unified.yaml"
DEFAULT_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
SMOKE_IMAGE = REPO_ROOT / "data" / "multimodal-rag" / "slide-01.png"

# Reference metrics from Task 05 (multimodal-b-caption.md, 2026-07-10)
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

B_COST_REFERENCE = {
    "nemotron": {"build_time_s": 606.29, "est_cost_usd": 0.006022},
    "gemini": {"build_time_s": 398.53, "est_cost_usd": 0.021415},
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


def write_report(
    path: Path,
    *,
    preflight_status: str,
    smoke_dim: int,
    run_payload: dict[str, object],
    timestamp: str,
) -> None:
    aggregates = run_payload["aggregates"]
    model_id = str(run_payload["embed_model"])
    build_time_s = float(run_payload["build_time_s"])
    est_cost_usd = float(run_payload["est_cost_usd"])

    lines = [
        "# Multimodal RAG — method C Unified Embed (Task 06)",
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
        f"| Pre-flight | {preflight_status} |",
        f"| embedding_dim (smoke) | {smoke_dim} |",
        f"| collection | `{run_payload['collection']}` |",
        f"| corpus_dir | `{run_payload['corpus_dir']}` |",
        "",
        "Index: PNG → VL image embed (без промежуточного текста).",
        "Query: VL text embed (та же модель).",
        "",
        "## Retrieval C по сегментам",
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
            "## C vs B по сегментам",
            "",
            "B reference: [multimodal-b-caption.md](multimodal-b-caption.md) "
            "(Task 05, 2026-07-10).",
            "",
            "| Сегмент | C Recall@5 | C nDCG@5 | B_nemotron R/nDCG | B_gemini R/nDCG | "
            "best B R/nDCG | Δ Recall (C−best B) |",
            "|---|---:|---:|---|---|---:|---:|",
        ],
    )

    for segment, agg in sorted(aggregates.items()):
        c_r = float(agg["recall_at_k"])
        c_n = float(agg["ndcg_at_5"])
        n = B_REFERENCE["nemotron"].get(segment, {})
        g = B_REFERENCE["gemini"].get(segment, {})
        n_r = n.get("recall_at_k")
        n_n = n.get("ndcg_at_5")
        g_r = g.get("recall_at_k")
        g_n = g.get("ndcg_at_5")
        best_r, best_n = _best_b_metrics(segment)
        if best_r is not None:
            delta = c_r - best_r
            delta_cell = f"{delta:+.3f}"
            best_cell = f"{best_r:.3f}/{best_n:.3f}" if best_n is not None else f"{best_r:.3f}/—"
        else:
            delta_cell = "—"
            best_cell = "—"
        n_cell = f"{n_r:.3f}/{n_n:.3f}" if n_r is not None and n_n is not None else "—"
        g_cell = f"{g_r:.3f}/{g_n:.3f}" if g_r is not None and g_n is not None else "—"
        lines.append(
            f"| {segment} | {c_r:.3f} | {c_n:.3f} | {n_cell} | {g_cell} | "
            f"{best_cell} | {delta_cell} |",
        )

    size = run_payload.get("index_size_mb")
    size_cell = f"{float(size):.3f}" if isinstance(size, (int, float)) and size is not None else "—"
    embed_t = run_payload.get("embed_time_s")
    upsert_t = run_payload.get("upsert_time_s")
    embed_cell = f"{float(embed_t):.2f}" if embed_t is not None else "—"
    upsert_cell = f"{float(upsert_t):.2f}" if upsert_t is not None else "—"

    lines.extend(
        [
            "",
            "## Время и стоимость",
            "",
            "| Метод | build_time_s | embed_time_s | upsert_time_s | index_size_mb | "
            "api_calls | est_cost_usd |",
            "|---|---:|---:|---:|---:|---:|---:|",
            f"| C (unified) | {build_time_s:.2f} | {embed_cell} | {upsert_cell} | "
            f"{size_cell} | {int(run_payload.get('api_calls', 0))} | {est_cost_usd:.6f} |",
            f"| B nemotron | {B_COST_REFERENCE['nemotron']['build_time_s']:.2f} | — | — | "
            f"0.193 | 66 | {B_COST_REFERENCE['nemotron']['est_cost_usd']:.6f} |",
            f"| B gemini | {B_COST_REFERENCE['gemini']['build_time_s']:.2f} | — | — | "
            f"0.193 | 66 | {B_COST_REFERENCE['gemini']['est_cost_usd']:.6f} |",
            "",
            "## Гипотеза MIRACL-Vision / русский S1",
            "",
        ],
    )

    s1 = aggregates.get("S1_text", {})
    c_s1_r = float(s1.get("recall_at_k", 0.0))
    c_s1_n = float(s1.get("ndcg_at_5", 0.0))
    n_s1_r = B_REFERENCE["nemotron"]["S1_text"]["recall_at_k"]
    n_s1_n = B_REFERENCE["nemotron"]["S1_text"]["ndcg_at_5"]
    g_s1_r = B_REFERENCE["gemini"]["S1_text"]["recall_at_k"]
    g_s1_n = B_REFERENCE["gemini"]["S1_text"]["ndcg_at_5"]
    best_s1_r = max(n_s1_r, g_s1_r)
    best_s1_n = max(n_s1_n, g_s1_n)

    hypothesis_confirmed = c_s1_r < best_s1_r or c_s1_n < best_s1_n
    verdict = "подтверждена" if hypothesis_confirmed else "опровергнута"

    lines.extend(
        [
            "Гипотеза: unified image-embedder проседает на плотном кириллическом S1 "
            "(слайды 2, 8, 13 — см. analysis.md) относительно B (caption + e5).",
            "",
            f"**Вердикт: {verdict}.**",
            "",
            f"- C S1_text: Recall@5={c_s1_r:.3f}, nDCG@5={c_s1_n:.3f} (n={int(s1.get('n', 0))})",
            f"- B nemotron S1: Recall@5={n_s1_r:.3f}, nDCG@5={n_s1_n:.3f}",
            f"- B gemini S1: Recall@5={g_s1_r:.3f}, nDCG@5={g_s1_n:.3f}",
            f"- best B S1: Recall@5={best_s1_r:.3f}, nDCG@5={best_s1_n:.3f}",
            f"- Δ Recall@5 (C − best B): {c_s1_r - best_s1_r:+.3f}",
            f"- Δ nDCG@5 (C − best B): {c_s1_n - best_s1_n:+.3f}",
            "",
            "## Вывод",
            "",
        ],
    )

    if hypothesis_confirmed:
        lines.append(
            f"Метод C **не обгоняет** лучший B на S1_text "
            f"(C {c_s1_r:.3f} vs best B {best_s1_r:.3f} Recall@5). "
            "Image-embed без текстового слоя не компенсирует плотный русский текст на слайдах."
        )
    else:
        lines.append(
            f"Метод C **обгоняет или равен** лучшему B на S1_text "
            f"(C {c_s1_r:.3f} vs best B {best_s1_r:.3f} Recall@5). "
            "Гипотеза просадки на русском для этого корпуса не подтвердилась."
        )

    lines.extend(
        [
            "",
            "Решение по сегментам, не macro-average. Сравнение с B: "
            "[multimodal-b-caption.md](multimodal-b-caption.md).",
            "",
        ],
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _prior_index_stats(config_id: str) -> dict[str, object] | None:
    runs_dir = REPO_ROOT / "evals" / "reports" / "runs"
    for path in sorted(runs_dir.glob("multimodal-c-unified-*.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("config_id") != config_id:
            continue
        if float(data.get("build_time_s", 0.0)) > 0:
            return data
    return None


def run_eval(*, skip_index: bool) -> tuple[dict[str, object], int]:
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

    if not skip_index:
        index_cost = indexer.build_index(cfg.corpus_dir)
        build_time_s = index_cost.build_time_s
        est_cost_usd = index_cost.est_cost_usd
        index_size_mb = index_cost.index_size_mb
        indexed_slides = getattr(indexer, "indexed_slides", 0)
        api_calls = index_cost.api_calls
        embed_time_s = getattr(indexer, "embed_time_s", None)
        upsert_time_s = getattr(indexer, "upsert_time_s", None)
        logger.info(
            "Indexed C: %d slides in %.2fs ($%.6f)",
            indexed_slides,
            build_time_s,
            est_cost_usd,
        )
    else:
        prior = _prior_index_stats(cfg.config_id)
        if prior:
            build_time_s = float(prior.get("build_time_s", 0.0))
            est_cost_usd = float(prior.get("est_cost_usd", 0.0))
            index_size_mb = prior.get("index_size_mb")
            indexed_slides = int(prior.get("indexed_slides", 0))
            api_calls = int(prior.get("api_calls", 0))
            embed_time_s = prior.get("embed_time_s")
            upsert_time_s = prior.get("upsert_time_s")

    embedder = VLEmbedder(model_id)
    client = QdrantClient(url=cfg.qdrant_url)
    dataset = load_multimodal_dataset(cfg.dataset_path)
    item_rows, aggregates = run_retrieval_eval(cfg, dataset, embedder=embedder, client=client)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_name = f"multimodal-c-unified-{timestamp}.json"
    run_path = REPO_ROOT / "evals" / "reports" / "runs" / run_name
    run_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "config_id": cfg.config_id,
        "embed_model": model_id,
        "collection": cfg.collection,
        "corpus_dir": _rel(cfg.corpus_dir),
        "build_time_s": build_time_s,
        "embed_time_s": embed_time_s,
        "upsert_time_s": upsert_time_s,
        "est_cost_usd": est_cost_usd,
        "api_calls": api_calls,
        "index_size_mb": index_size_mb,
        "indexed_slides": indexed_slides,
        "aggregates": aggregates,
        "items": item_rows,
    }
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Run JSON: %s", run_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Method C unified VL embed eval")
    parser.add_argument("--skip-index", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    cfg = load_multimodal_config(CONFIG_PATH)
    model_id = cfg.embedding_model

    preflight_status = preflight_model(model_id) if not args.skip_preflight else "SKIPPED"
    logger.info("Pre-flight %s: %s", model_id, preflight_status)

    smoke_dim = cfg.embedding_dim
    if not args.skip_smoke and SMOKE_IMAGE.exists():
        logger.info("Smoke VL embed on slide-01 (validates API access)")
        try:
            result = smoke_embed(model_id, SMOKE_IMAGE)
        except Exception as exc:
            msg = f"VL embed smoke failed for {model_id}: {exc}"
            raise RuntimeError(msg) from exc
        smoke_dim = len(result.vector)
        logger.info(
            "Smoke OK: dim=%d, $%.6f, %.2fs",
            smoke_dim,
            result.est_cost_usd,
            result.latency_s,
        )
        if smoke_dim != cfg.embedding_dim:
            msg = (
                f"Config embedding_dim={cfg.embedding_dim} but smoke returned "
                f"dim={smoke_dim}; update multimodal-c-unified.yaml"
            )
            raise RuntimeError(msg)
        if preflight_status == "NOT_IN_CATALOG":
            preflight_status = "SMOKE_OK_NOT_IN_CATALOG"
    elif preflight_status == "NOT_IN_CATALOG":
        msg = (
            f"Model {model_id} not in OpenRouter catalog and smoke skipped; "
            "run without --skip-smoke"
        )
        raise RuntimeError(msg)

    run_payload = run_eval(skip_index=args.skip_index)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_path = REPO_ROOT / "evals" / "reports" / "multimodal-c-unified.md"
    write_report(
        report_path,
        preflight_status=preflight_status,
        smoke_dim=smoke_dim,
        run_payload=run_payload,
        timestamp=timestamp,
    )
    logger.info("Report: %s", report_path)


if __name__ == "__main__":
    main()
