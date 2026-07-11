"""Tests for Jina multivector client parsing."""

from __future__ import annotations

import pytest

from indexers.jina_multivector.client import _parse_multivector_embedding


def test_parse_nested_multivector() -> None:
    raw = [[0.1, 0.2], [0.3, 0.4]]
    vectors = _parse_multivector_embedding(raw, token_dim=2)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_flat_multivector() -> None:
    raw = [0.1, 0.2, 0.3, 0.4]
    vectors = _parse_multivector_embedding(raw, token_dim=2)
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_parse_wrong_dim_raises() -> None:
    with pytest.raises(RuntimeError, match="token_dim"):
        _parse_multivector_embedding([[0.1, 0.2, 0.3]], token_dim=2)
