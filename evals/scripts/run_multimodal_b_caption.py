"""Orchestrate method B: two VLM models, hallucination check, retrieval eval, report."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client import QdrantClient

from indexers.caption.factory import preflight_models, smoke_caption
from indexers.caption.pricing import model_slug
from indexers.config import EVALS_ROOT, REPO_ROOT
from indexers.factory import load_multimodal_config, make_indexer
from scripts.caption_hallucination_check import run_checks, write_hallucination_report
from scripts.multimodal_models import load_multimodal_dataset
from scripts.multimodal_retrieval import E5Embedder, run_retrieval_eval

logger = logging.getLogger(__name__)

ENGINE_CONFIGS: tuple[tuple[str, Path, str], ...] = (
    (
        "nemotron",
        EVALS_ROOT / "configs" / "multimodal-b-caption-nemotron.yaml",
        "nvidia/nemotron-nano-12b-v2-vl:free",
    ),
    (
        "gemini",
        EVALS_ROOT / "configs" / "multimodal-b-caption-gemini.yaml",
        "google/gemini-2.5-flash-lite",
    ),
)

SMOKE_IMAGE = REPO_ROOT / "data" / "multimodal-rag" / "slide-01.png"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_combined_report(
    path: Path,
    *,
    preflight: dict[str, str],
    hallucination_checks: list,
    run_payloads: dict[str, dict[str, object]],
    timestamp: str,
) -> None:
    lines = [
        "# Multimodal RAG — method B Caption (Task 05)",
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
        "| Модель | model_id | Pre-flight | Коллекция | artifact_dir |",
        "|---|---|---|---|---|",
    ]

    for engine, payload in run_payloads.items():
        model_id = str(payload["caption_model"])
        status = preflight.get(model_id, "—")
        lines.append(
            f"| {engine} | `{model_id}` | {status} | `{payload['collection']}` | "
            f"`{payload['artifact_dir']}` |",
        )

    lines.extend(
        [
            "",
            "Промпт: русский, дословное извлечение чисел, temperature=0.",
            "Embedding: `intfloat/multilingual-e5-base` (768d, local, $0).",
        ],
    )

    nemotron_artifact = REPO_ROOT / "evals" / "artifacts" / "captions" / "nemotron-nano-12b-v2-vl"
    fallback_count = 0
    if nemotron_artifact.is_dir():
        for path in nemotron_artifact.glob("slide-*.txt"):
            text = path.read_text(encoding="utf-8")
            if "# fallback_from:" in text:
                fallback_count += 1
    if fallback_count:
        lines.append(
            f"- **Nemotron rate limit:** slides 50–66 через fallback "
            f"`qwen/qwen3-vl-8b-instruct` ({fallback_count} artifacts, "
            "причина: `rate_limit_429_free_tier`).",
        )

    lines.extend(
        [
            "",
            "## Hallucination-check (S2 slides 10–11)",
            "",
            "Детали: `evals/artifacts/captions/hallucination-check.md`",
            "",
            "| Слайд | Модель | Вердикт |",
            "|---:|---|---|",
        ],
    )

    for check in hallucination_checks:
        lines.append(f"| {check.slide_id} | {check.model_key} | **{check.verdict}** |")

    lines.extend(["", "## Retrieval по сегментам", ""])

    for engine, payload in run_payloads.items():
        lines.append(f"### {engine}")
        lines.append("")
        lines.append(
            "| Сегмент | n | Recall@k | nDCG@5 | MRR | Set-Recall@k | trap_in_topk |",
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        aggregates = payload["aggregates"]
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
        lines.append("")

    lines.extend(
        [
            "## Время и стоимость",
            "",
            "| Модель | build_time_s | caption_time_s | embed_time_s | "
            "index_size_mb | api_calls | est_cost_usd |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ],
    )

    nemotron_time = float(run_payloads.get("nemotron", {}).get("build_time_s", 0.0))
    for engine, payload in run_payloads.items():
        size = payload.get("index_size_mb")
        size_cell = f"{size:.3f}" if isinstance(size, (int, float)) and size is not None else "—"
        caption_t = payload.get("caption_time_s")
        embed_t = payload.get("embed_time_s")
        caption_cell = f"{float(caption_t):.2f}" if caption_t is not None else "—"
        embed_cell = f"{float(embed_t):.2f}" if embed_t is not None else "—"
        lines.append(
            f"| {engine} | {float(payload['build_time_s']):.2f} | {caption_cell} | "
            f"{embed_cell} | {size_cell} | {int(payload.get('api_calls', 0))} | "
            f"{float(payload['est_cost_usd']):.6f} |",
        )

    gemini_time = float(run_payloads.get("gemini", {}).get("build_time_s", 0.0))
    speed_ratio = gemini_time / nemotron_time if nemotron_time > 0 else 0.0

    n_s2_r = (
        run_payloads.get("nemotron", {})
        .get("aggregates", {})
        .get("S2_chart", {})
        .get(
            "recall_at_k",
            0.0,
        )
    )
    g_s2_r = (
        run_payloads.get("gemini", {})
        .get("aggregates", {})
        .get("S2_chart", {})
        .get(
            "recall_at_k",
            0.0,
        )
    )
    n_s2_n = (
        run_payloads.get("nemotron", {})
        .get("aggregates", {})
        .get("S2_chart", {})
        .get(
            "ndcg_at_5",
            0.0,
        )
    )
    g_s2_n = (
        run_payloads.get("gemini", {})
        .get("aggregates", {})
        .get("S2_chart", {})
        .get(
            "ndcg_at_5",
            0.0,
        )
    )
    n_s3_r = (
        run_payloads.get("nemotron", {})
        .get("aggregates", {})
        .get("S3_layout", {})
        .get(
            "recall_at_k",
            0.0,
        )
    )
    g_s3_r = (
        run_payloads.get("gemini", {})
        .get("aggregates", {})
        .get("S3_layout", {})
        .get(
            "recall_at_k",
            0.0,
        )
    )
    n_s3_n = (
        run_payloads.get("nemotron", {})
        .get("aggregates", {})
        .get("S3_layout", {})
        .get(
            "ndcg_at_5",
            0.0,
        )
    )
    g_s3_n = (
        run_payloads.get("gemini", {})
        .get("aggregates", {})
        .get("S3_layout", {})
        .get(
            "ndcg_at_5",
            0.0,
        )
    )

    n_cost = float(run_payloads.get("nemotron", {}).get("est_cost_usd", 0.0))
    g_cost = float(run_payloads.get("gemini", {}).get("est_cost_usd", 0.0))

    s2_gain = g_s2_r > n_s2_r or g_s2_n > n_s2_n
    s3_gain = g_s3_r > n_s3_r or g_s3_n > n_s3_n
    justified = s2_gain or s3_gain

    lines.extend(
        [
            "",
            f"Speed ratio (gemini/nemotron): **{speed_ratio:.2f}×** "
            f"(nemotron={nemotron_time:.1f}s, gemini={gemini_time:.1f}s).",
            "",
            "## Вывод",
            "",
            f"**Оправдывает ли мощная модель (gemini) прирост качества?** "
            f"**{'Да' if justified else 'Нет'}** — по S2/S3:",
            "",
            f"- S2_chart: nemotron Recall@5={n_s2_r:.3f} nDCG@5={n_s2_n:.3f}; "
            f"gemini Recall@5={g_s2_r:.3f} nDCG@5={g_s2_n:.3f}.",
            f"- S3_layout: nemotron Recall@5={n_s3_r:.3f} nDCG@5={n_s3_n:.3f}; "
            f"gemini Recall@5={g_s3_r:.3f} nDCG@5={g_s3_n:.3f}.",
            f"- Стоимость индексации: nemotron=${n_cost:.6f}, gemini=${g_cost:.6f}.",
            f"- Скорость: gemini {'медленнее' if speed_ratio > 1 else 'быстрее'} "
            f"nemotron в {speed_ratio:.2f}× по build_time_s.",
            "- Решение по сегментам, не macro-average по корпусу.",
            "",
            "## Артефакты для ручной проверки",
            "",
            f"- Nemotron: `{_rel(REPO_ROOT / 'evals/artifacts/captions/nemotron-nano-12b-v2-vl')}`",
            f"- Gemini: `{_rel(REPO_ROOT / 'evals/artifacts/captions/gemini-2.5-flash-lite')}`",
            "- Смотреть S2 (10–11) и S3 (15, 32) на адекватность подписей vs generic-описания.",
            "",
        ],
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _prior_index_stats(config_id: str) -> dict[str, object] | None:
    runs_dir = REPO_ROOT / "evals" / "reports" / "runs"
    for path in sorted(runs_dir.glob("multimodal-b-caption-*.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("config_id") != config_id:
            continue
        if float(data.get("build_time_s", 0.0)) > 0:
            return data
    return None


def run_engine(
    engine: str,
    config_path: Path,
    model_id: str,
    *,
    skip_index: bool,
) -> dict[str, object]:
    cfg = load_multimodal_config(config_path)
    indexer = make_indexer(cfg)

    build_time_s = 0.0
    est_cost_usd = 0.0
    index_size_mb = None
    indexed_slides = 0
    api_calls = 0
    caption_time_s = None
    embed_time_s = None

    if not skip_index:
        index_cost = indexer.build_index(cfg.corpus_dir)
        build_time_s = index_cost.build_time_s
        est_cost_usd = index_cost.est_cost_usd
        index_size_mb = index_cost.index_size_mb
        indexed_slides = getattr(indexer, "indexed_slides", 0)
        api_calls = index_cost.api_calls
        caption_time_s = getattr(indexer, "caption_time_s", None)
        embed_time_s = getattr(indexer, "embed_time_s", None)
        logger.info(
            "Indexed %s: %d slides in %.2fs ($%.6f)",
            engine,
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
            caption_time_s = prior.get("caption_time_s")
            embed_time_s = prior.get("embed_time_s")
        elif cfg.artifact_dir and cfg.artifact_dir.is_dir():
            indexed_slides = len(list(cfg.artifact_dir.glob("slide-*.txt")))

    embedder = E5Embedder(cfg.embedding_model)
    client = QdrantClient(url=cfg.qdrant_url)
    dataset = load_multimodal_dataset(cfg.dataset_path)
    item_rows, aggregates = run_retrieval_eval(cfg, dataset, embedder=embedder, client=client)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    slug = model_slug(model_id)
    run_name = f"multimodal-b-caption-{slug}-{timestamp}.json"
    run_path = REPO_ROOT / "evals" / "reports" / "runs" / run_name
    run_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config_id": cfg.config_id,
        "engine": engine,
        "caption_model": model_id,
        "collection": cfg.collection,
        "artifact_dir": _rel(cfg.artifact_dir) if cfg.artifact_dir else None,
        "build_time_s": build_time_s,
        "caption_time_s": caption_time_s,
        "embed_time_s": embed_time_s,
        "est_cost_usd": est_cost_usd,
        "api_calls": api_calls,
        "index_size_mb": index_size_mb,
        "indexed_slides": indexed_slides,
        "aggregates": aggregates,
        "items": item_rows,
    }
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Method B caption eval (both VLMs)")
    parser.add_argument("--skip-index", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    model_ids = [model_id for _, _, model_id in ENGINE_CONFIGS]
    preflight = (
        preflight_models(model_ids)
        if not args.skip_preflight
        else dict.fromkeys(model_ids, "SKIPPED")
    )
    for model_id, status in preflight.items():
        logger.info("Pre-flight %s: %s", model_id, status)
        if status == "MISSING":
            msg = f"Model not available on OpenRouter: {model_id}"
            raise RuntimeError(msg)

    if not args.skip_preflight and not args.skip_smoke and SMOKE_IMAGE.exists():
        for engine, _, model_id in ENGINE_CONFIGS:
            logger.info("Smoke caption %s on slide-01", engine)
            result = smoke_caption(model_id, SMOKE_IMAGE)
            logger.info(
                "Smoke OK %s: %d chars, $%.6f, %.2fs",
                engine,
                len(result.text),
                result.est_cost_usd,
                result.latency_s,
            )

    run_payloads: dict[str, dict[str, object]] = {}
    for engine, config_path, model_id in ENGINE_CONFIGS:
        run_payloads[engine] = run_engine(
            engine,
            config_path,
            model_id,
            skip_index=args.skip_index,
        )

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    hallucination_checks = run_checks()
    hallucination_path = REPO_ROOT / "evals" / "artifacts" / "captions" / "hallucination-check.md"
    write_hallucination_report(hallucination_path, hallucination_checks, timestamp=timestamp)
    logger.info("Hallucination check: %s", hallucination_path)

    report_path = REPO_ROOT / "evals" / "reports" / "multimodal-b-caption.md"
    write_combined_report(
        report_path,
        preflight=preflight,
        hallucination_checks=hallucination_checks,
        run_payloads=run_payloads,
        timestamp=timestamp,
    )
    logger.info("Report: %s", report_path)


if __name__ == "__main__":
    main()
