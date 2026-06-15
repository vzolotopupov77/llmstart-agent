# Шаблон: evals/tests/test_dataset_integrity.py (E-15)
# Integrity-ассерты на сам датасет (не unit-тесты логики):
# опечатка в манифесте должна падать здесь, а не в середине прогона.

from evals.scripts.models import load_manifest  # Pydantic-loader (E-15)

MANIFEST = "evals/datasets/e2e/e2e-qa/v001_2026-06-10.yaml"


def test_e2e_qa_integrity():
    ds = load_manifest(MANIFEST)

    # Размер и уникальность ключей upsert
    assert len(ds.items) >= 10
    assert len({i.id for i in ds.items}) == len(ds.items), "дубликаты id"

    for item in ds.items:
        # Гейт human review (E-13)
        assert item.metadata.reviewed_by, f"{item.id}: нет reviewed_by (E-13)"
        # Честность ground truth (E-14)
        assert item.metadata.gt_quality in ("verified", "approximate")
        # Доменные enum'ы
        assert item.metadata.segment in ("b2c", "b2b")
        assert item.metadata.source in ("real_dialog", "synthetic")
        # Читаемость эталона (E-12): эталон — структура/текст, не код
        if item.expected_output is not None:
            assert not isinstance(item.expected_output, (int, bytes)), \
                f"{item.id}: эталон не читается без декодера (E-12)"


def test_version_files_immutable():
    """Версии-снимки не редактируются: имя файла соответствует version внутри (E-11)."""
    ds = load_manifest(MANIFEST)
    assert ds.version in MANIFEST, "version в манифесте не совпадает с именем файла"
