"""Generic multimodal RAG eval runner: config → index → retrieval eval → report."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client import QdrantClient

from indexers.config import EVALS_ROOT, REPO_ROOT
from indexers.factory import load_multimodal_config, make_indexer
from scripts.multimodal_models import load_multimodal_dataset
from scripts.multimodal_retrieval import E5Embedder, run_retrieval_eval

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = EVALS_ROOT / "configs" / "multimodal-baseline.yaml"

INGESTION_FAILURE_EXAMPLES: tuple[dict[str, str | int | float], ...] = (
    {
        "slide": 10,
        "golden": "72% (Zapier)",
        "pdf_chars": 0,
        "item": "S2-9",
        "recall_note": "0.000",
    },
    {
        "slide": 11,
        "golden": "70% документооборот, 39% заголовок",
        "pdf_chars": 0,
        "item": "S2-1",
        "recall_note": "шум (Recall=1.0 случайно, rank 3)",
    },
    {
        "slide": 9,
        "golden": "~45% Epoch AI 2026",
        "pdf_chars": 0,
        "item": "S2-3",
        "recall_note": "0.000",
    },
)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_report(
    path: Path,
    *,
    config_id: str,
    cfg_corpus_dir: Path,
    cfg_artifact_dir: Path | None,
    collection: str,
    embedding_model: str,
    embedding_dim: int,
    top_k: int,
    corpus_stats: dict[int, int],
    index_cost_build_time_s: float,
    indexed_slides: int,
    est_cost_usd: float,
    aggregates: dict[str, dict[str, float]],
    item_rows: list[dict[str, object]],
    report_slug: str,
) -> None:
    nonempty = sum(1 for count in corpus_stats.values() if count > 0)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_stamp = timestamp.replace(":", "").replace("-", "")

    sprint_link = "../../docs/sprints/sprint-10-multimodal-rag/README.md"
    metric_link = "../../docs/sprints/sprint-10-multimodal-rag/metric_map.md"
    artifact_cell = _rel(cfg_artifact_dir) if cfg_artifact_dir else "—"

    lines = [
        f"# Multimodal RAG — {report_slug} (Task 03)",
        "",
        f"> **Дата:** {timestamp[:10]} · **config:** `{config_id}`",
        f"> **Спринт:** [sprint-10-multimodal-rag]({sprint_link})",
        f"> **Metric map:** [metric_map.md]({metric_link})",
        "",
        "---",
        "",
        "## Конфигурация",
        "",
        "| Параметр | Значение |",
        "|---|---|",
        f"| collection | `{collection}` |",
        f"| embedding | `{embedding_model}` (dim={embedding_dim}) |",
        f"| top_k | {top_k} |",
        f"| corpus_dir (input) | `{_rel(cfg_corpus_dir)}` |",
        f"| artifact_dir (output) | `{artifact_cell}` |",
        f"| PDF text pages non-empty | {nonempty}/66 |",
        f"| indexed slides | {indexed_slides} |",
        f"| build_time_s | {index_cost_build_time_s:.2f} |",
        f"| est_cost_usd | {est_cost_usd:.2f} |",
        "",
        "## Ingestion failure examples (chart slides)",
        "",
        "Гипотеза: naive PDF text layer не извлекает числа с chart-слайдов → retrieval слеп.",
        "",
        "| Слайд | Число на PNG | PDF chars | Item | Recall@5 |",
        "|---:|---|---:|---|---:|",
    ]

    item_recall: dict[str, float] = {}
    for row in item_rows:
        item_id = row.get("id")
        if isinstance(item_id, str):
            item_recall[item_id] = float(row.get("recall_at_k", 0.0))

    for example in INGESTION_FAILURE_EXAMPLES:
        item_id = str(example["item"])
        recall_val = item_recall.get(item_id, 0.0)
        if example["recall_note"] != "0.000":
            recall_cell = str(example["recall_note"])
        elif int(example["pdf_chars"]) == 0 and recall_val > 0:
            recall_cell = f"{recall_val:.3f} ⚠️ шум"
        else:
            recall_cell = f"{recall_val:.3f}"
        lines.append(
            f"| {example['slide']} | {example['golden']} | {example['pdf_chars']} | "
            f"{example['item']} | {recall_cell} |",
        )

    lines.extend(
        [
            "",
        ],
    )
    s2_agg = aggregates.get("S2_chart", {}).get("recall_at_k")
    if s2_agg is not None:
        lines.append(
            f"S2_chart aggregate Recall@5 = {s2_agg:.3f} — "
            "**шум** пустого индекса, не сигнал качества.",
        )
    lines.extend(
        [
            "",
            "## Retrieval по сегментам (primary)",
            "",
            "> ⚠️ Не использовать macro-average по корпусу для решений — только строки таблицы.",
            "",
            "| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk (S5 diag) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ],
    )

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
            "## Интерпретация",
            "",
            f"- PDF text layer: **{nonempty}** из 66 страниц с текстом — "
            "naive baseline индексирует пустые passage; "
            "метрики отражают «слепоту» без OCR/caption.",
            "- **S5:** primary metric = `correct_refusal_rate` (generation); "
            "`trap_slide_in_topk` — только retrieval-диагностика.",
            "",
            "## Ingestion / Generation",
            "",
            "- **CER / TEDS** — не применимы к baseline (Task 04 / Task 07).",
            "- **Generation** — не прогонялся (retrieval-only).",
            "",
            "---",
            "",
            f"Детали: `evals/reports/runs/multimodal-baseline-{run_stamp}.json`",
            "",
        ],
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    json_path = path.parent / "runs" / f"multimodal-baseline-{run_stamp}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {
                "config_id": config_id,
                "timestamp": timestamp,
                "corpus_nonempty_pages": nonempty,
                "build_time_s": index_cost_build_time_s,
                "aggregates": aggregates,
                "items": item_rows,
                "ingestion_failure_examples": list(INGESTION_FAILURE_EXAMPLES),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Multimodal RAG eval (indexer registry)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--skip-index", action="store_true")
    parser.add_argument("--index-only", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config_path = args.config if args.config.is_absolute() else EVALS_ROOT / args.config
    cfg = load_multimodal_config(config_path)
    indexer = make_indexer(cfg)

    build_time_s = 0.0
    indexed_slides = 0
    est_cost_usd = 0.0
    corpus_stats: dict[int, int] = {}

    if not args.skip_index:
        index_cost = indexer.build_index(cfg.corpus_dir)
        build_time_s = index_cost.build_time_s
        est_cost_usd = index_cost.est_cost_usd
        indexed_slides = getattr(indexer, "indexed_slides", 0)
        corpus_stats = getattr(indexer, "corpus_stats", {})
        nonempty = sum(1 for c in corpus_stats.values() if c > 0)
        logger.info(
            "Indexed %d slides in %.2fs (%d pages with PDF text)",
            indexed_slides,
            build_time_s,
            nonempty,
        )
    elif cfg.artifact_dir and cfg.artifact_dir.is_dir():
        from scripts.multimodal_retrieval import strip_corpus_header

        for path in sorted(cfg.artifact_dir.glob("slide-*.txt")):
            slide_id = int(path.stem.split("-")[1])
            body = path.read_text(encoding="utf-8")
            corpus_stats[slide_id] = len(strip_corpus_header(body))
        indexed_slides = len(corpus_stats)

    if args.index_only:
        return

    embedder = E5Embedder(cfg.embedding_model)
    client = QdrantClient(url=cfg.qdrant_url)
    dataset = load_multimodal_dataset(cfg.dataset_path)
    item_rows, aggregates = run_retrieval_eval(cfg, dataset, embedder=embedder, client=client)

    report_name = (
        "multimodal-baseline.md"
        if cfg.config_id == "multimodal-baseline"
        else f"{cfg.config_id}.md"
    )
    report_path = REPO_ROOT / "evals" / "reports" / report_name
    write_report(
        report_path,
        config_id=cfg.config_id,
        cfg_corpus_dir=cfg.corpus_dir,
        cfg_artifact_dir=cfg.artifact_dir,
        collection=cfg.collection,
        embedding_model=cfg.embedding_model,
        embedding_dim=cfg.embedding_dim,
        top_k=cfg.top_k,
        corpus_stats=corpus_stats,
        index_cost_build_time_s=build_time_s,
        indexed_slides=indexed_slides,
        est_cost_usd=est_cost_usd,
        aggregates=aggregates,
        item_rows=item_rows,
        report_slug="naive text baseline",
    )
    logger.info("Report: %s", report_path)


if __name__ == "__main__":
    main()
