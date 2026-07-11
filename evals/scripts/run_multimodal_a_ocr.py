"""Orchestrate method A: two OCR engines, CER, retrieval eval, combined report."""

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
from scripts.ocr_cer import CerEngineReport, load_golden_manifest, score_engine

logger = logging.getLogger(__name__)

ENGINE_CONFIGS: tuple[tuple[str, Path], ...] = (
    ("tesseract", EVALS_ROOT / "configs" / "multimodal-a-ocr-tesseract.yaml"),
    ("rapidocr", EVALS_ROOT / "configs" / "multimodal-a-ocr-modern.yaml"),
)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _format_cer_table(reports: dict[str, CerEngineReport]) -> list[str]:
    engines = list(reports.keys())
    slides = [score.slide_id for score in reports[engines[0]].scores]
    header = "| slide | segment | " + " | ".join(engines) + " |"
    sep = "|---:|---|" + "|".join(["---:"] * len(engines)) + "|"
    lines = [header, sep]
    segment_by_slide = {
        score.slide_id: score.segment for score in reports[engines[0]].scores
    }
    for slide_id in slides:
        row_cells = []
        for engine in engines:
            match = next(s for s in reports[engine].scores if s.slide_id == slide_id)
            row_cells.append(f"{match.cer:.3f}")
        lines.append(
            f"| {slide_id} | {segment_by_slide[slide_id]} | "
            + " | ".join(row_cells)
            + " |",
        )
    return lines


def write_combined_report(
    path: Path,
    *,
    cer_reports: dict[str, CerEngineReport],
    run_payloads: dict[str, dict[str, object]],
    timestamp: str,
) -> None:
    manifest = load_golden_manifest()
    slide_list = ", ".join(str(entry["slide_id"]) for entry in manifest["slides"])

    lines = [
        "# Multimodal RAG — method A OCR (Task 04)",
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
        "| Движок | OCR | Коллекция | artifact_dir |",
        "|---|---|---|---|",
    ]

    for engine, payload in run_payloads.items():
        lines.append(
            f"| {engine} | {payload['ocr_engine']} | `{payload['collection']}` | "
            f"`{payload['artifact_dir']}` |",
        )

    lines.extend(
        [
            "",
            "Pre-process: adaptive invert if mean luminance < 128, contrast ×1.5.",
            "Tesseract: `lang=rus+eng`, `psm=6`. Modern: RapidOCR ONNX (`rapidocr-onnxruntime`).",
            "Runtime: tesseract=`docker`, rapidocr=`local` "
            "(EasyOCR/RapidOCR docker blocked by PyPI in build).",
            "",
            "## CER (ingestion-quality)",
            "",
            "**Формула:** `CER = Levenshtein(ref, hyp) / len(ref)` после normalize "
            "(lowercase, collapse whitespace; punctuation и `%` сохраняются).",
            f"**Выборка ({len(manifest['slides'])} слайдов):** {slide_list}.",
            "CER > 1.0 возможен при галлюцинации символов — не clamp.",
            "",
        ],
    )

    for engine, report in cer_reports.items():
        lines.append(
            f"**{engine}:** mean={report.mean_cer:.3f}, median={report.median_cer:.3f}",
        )
    lines.append("")
    lines.extend(_format_cer_table(cer_reports))
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
            "| Движок | build_time_s | index_size_mb | est_cost_usd |",
            "|---|---:|---:|---:|",
        ],
    )
    for engine, payload in run_payloads.items():
        size = payload.get("index_size_mb")
        size_cell = f"{size:.3f}" if isinstance(size, (int, float)) and size is not None else "—"
        lines.append(
            f"| {engine} | {payload['build_time_s']:.2f} | {size_cell} | "
            f"{payload['est_cost_usd']:.2f} |",
        )

    t_mean = cer_reports["tesseract"].mean_cer
    m_mean = cer_reports["rapidocr"].mean_cer
    better_ingestion = "rapidocr" if m_mean < t_mean else "tesseract"

    t_s1 = run_payloads["tesseract"]["aggregates"].get("S1_text", {}).get("recall_at_k", 0.0)
    m_s1 = run_payloads["rapidocr"]["aggregates"].get("S1_text", {}).get("recall_at_k", 0.0)
    t_s2 = run_payloads["tesseract"]["aggregates"].get("S2_chart", {}).get("recall_at_k", 0.0)
    m_s2 = run_payloads["rapidocr"]["aggregates"].get("S2_chart", {}).get("recall_at_k", 0.0)
    better_retrieval = "rapidocr" if (m_s1 + m_s2) > (t_s1 + t_s2) else "tesseract"

    lines.extend(
        [
            "",
            "## Вывод",
            "",
            "Modern engine: **RapidOCR (ONNX)** — EasyOCR docker build blocked by PyPI "
            "network errors in this environment; RapidOCR per plan fallback.",
            "",
            f"- **Ingestion (CER mean):** `{better_ingestion}` "
            f"(tesseract={t_mean:.3f}, rapidocr={m_mean:.3f}).",
            f"- **Retrieval (S1+S2 Recall@5):** `{better_retrieval}` "
            f"(tesseract S1={t_s1:.3f} S2={t_s2:.3f}; "
            f"rapidocr S1={m_s1:.3f} S2={m_s2:.3f}).",
            "- Решение по сегментам, не macro-average по корпусу.",
            "",
            "## Типичные ошибки (ручная проверка)",
            "",
            f"- Tesseract: `{_rel(REPO_ROOT / 'evals/artifacts/ocr/tesseract')}`",
            f"- RapidOCR: `{_rel(REPO_ROOT / 'evals/artifacts/ocr/rapidocr')}`",
            "- Смотреть кириллицу, разрывы строк, chart-слайды 9–11 на тёмном фоне.",
            "",
        ],
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _prior_index_stats(config_id: str) -> dict[str, object] | None:
    runs_dir = REPO_ROOT / "evals" / "reports" / "runs"
    for path in sorted(runs_dir.glob("*.json"), reverse=True):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("config_id") != config_id:
            continue
        if float(data.get("build_time_s", 0.0)) > 0:
            return data
    return None


def run_engine(engine: str, config_path: Path, *, skip_index: bool) -> dict[str, object]:
    cfg = load_multimodal_config(config_path)
    indexer = make_indexer(cfg)

    build_time_s = 0.0
    est_cost_usd = 0.0
    index_size_mb = None
    indexed_slides = 0

    if not skip_index:
        index_cost = indexer.build_index(cfg.corpus_dir)
        build_time_s = index_cost.build_time_s
        est_cost_usd = index_cost.est_cost_usd
        index_size_mb = index_cost.index_size_mb
        indexed_slides = getattr(indexer, "indexed_slides", 0)
        logger.info(
            "Indexed %s: %d slides in %.2fs",
            engine,
            indexed_slides,
            build_time_s,
        )
    else:
        prior = _prior_index_stats(cfg.config_id)
        if prior:
            build_time_s = float(prior.get("build_time_s", 0.0))
            est_cost_usd = float(prior.get("est_cost_usd", 0.0))
            index_size_mb = prior.get("index_size_mb")
            indexed_slides = int(prior.get("indexed_slides", 0))
        elif cfg.artifact_dir and cfg.artifact_dir.is_dir():
            indexed_slides = len(list(cfg.artifact_dir.glob("slide-*.txt")))

    embedder = E5Embedder(cfg.embedding_model)
    client = QdrantClient(url=cfg.qdrant_url)
    dataset = load_multimodal_dataset(cfg.dataset_path)
    item_rows, aggregates = run_retrieval_eval(cfg, dataset, embedder=embedder, client=client)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_name = f"multimodal-a-ocr-{engine}-{timestamp}.json"
    run_path = REPO_ROOT / "evals" / "reports" / "runs" / run_name
    run_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "config_id": cfg.config_id,
        "engine": engine,
        "ocr_engine": cfg.ocr_engine,
        "collection": cfg.collection,
        "artifact_dir": _rel(cfg.artifact_dir) if cfg.artifact_dir else None,
        "build_time_s": build_time_s,
        "est_cost_usd": est_cost_usd,
        "index_size_mb": index_size_mb,
        "indexed_slides": indexed_slides,
        "aggregates": aggregates,
        "items": item_rows,
    }
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Method A OCR eval (both engines)")
    parser.add_argument("--skip-index", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_payloads: dict[str, dict[str, object]] = {}
    cer_reports: dict[str, CerEngineReport] = {}

    for engine, config_path in ENGINE_CONFIGS:
        run_payloads[engine] = run_engine(engine, config_path, skip_index=args.skip_index)
        cfg = load_multimodal_config(config_path)
        if cfg.artifact_dir is None:
            msg = f"artifact_dir missing for {engine}"
            raise ValueError(msg)
        cer_reports[engine] = score_engine(cfg.artifact_dir, engine=engine)

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_path = REPO_ROOT / "evals" / "reports" / "multimodal-a-ocr.md"
    write_combined_report(
        report_path,
        cer_reports=cer_reports,
        run_payloads=run_payloads,
        timestamp=timestamp,
    )
    logger.info("Report: %s", report_path)


if __name__ == "__main__":
    main()
