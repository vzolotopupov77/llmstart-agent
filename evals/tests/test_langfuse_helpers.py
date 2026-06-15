"""Tests for Langfuse helper URL/linking logic."""

from __future__ import annotations

from unittest.mock import MagicMock

from scripts.langfuse_helpers import dataset_run_ui_url, resolve_dataset_run_url


class _FakeClient:
    def _get_project_id(self) -> str:
        return "proj-123"


def test_dataset_run_ui_url() -> None:
    url = dataset_run_ui_url(
        "http://localhost:3001",
        project_id="proj-1",
        dataset_id="ds-1",
        dataset_run_id="run-1",
    )
    assert url == "http://localhost:3001/project/proj-1/datasets/ds-1/runs/run-1"


def test_resolve_dataset_run_url_prefers_sdk() -> None:
    client = _FakeClient()
    assert (
        resolve_dataset_run_url(
            client,
            dataset_run_id="run-1",
            dataset_id="ds-1",
            sdk_url="http://lf/existing",
        )
        == "http://lf/existing"
    )


def test_resolve_dataset_run_url_fallback(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3001")

    client = _FakeClient()
    url = resolve_dataset_run_url(
        client,
        dataset_run_id="run-abc",
        dataset_id="ds-xyz",
        sdk_url=None,
    )
    assert url == "http://localhost:3001/project/proj-123/datasets/ds-xyz/runs/run-abc"


def test_resolve_dataset_run_url_none_without_ids() -> None:
    client = MagicMock()
    assert (
        resolve_dataset_run_url(client, dataset_run_id=None, dataset_id="ds", sdk_url=None) is None
    )
