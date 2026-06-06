"""Mock payment state in data/payments.json."""

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from mcp_server.data_access.catalog import validate_product_id
from mcp_server.paths import payments_path

PaymentStatus = Literal["pending", "confirmed"]


class PaymentRecord(BaseModel):
    """Single mock payment session."""

    session_id: str
    product_id: str
    status: PaymentStatus
    url: str
    token: str
    created_at: str
    confirmed_at: str | None = None


class PaymentsStore(BaseModel):
    """All payment records keyed by composite id."""

    payments: dict[str, PaymentRecord] = Field(default_factory=dict)


def _payment_key(session_id: str, product_id: str) -> str:
    return f"{session_id}:{product_id}"


def _load_store(path: Path) -> PaymentsStore:
    if not path.exists():
        return PaymentsStore()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return PaymentsStore.model_validate(raw)


def _save_store(path: Path, store: PaymentsStore) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        store.model_dump_json(indent=2),
        encoding="utf-8",
    )


def create_payment_link(product_id: str, session_id: str) -> str:
    """Create or return existing mock checkout URL."""
    validate_product_id(product_id)
    path = payments_path()
    store = _load_store(path)
    key = _payment_key(session_id, product_id)

    existing = store.payments.get(key)
    if existing is not None:
        return existing.url

    token = secrets.token_urlsafe(16)
    url = (
        f"https://pay.mock.llmstart.ru/checkout"
        f"?product_id={product_id}&session_id={session_id}&token={token}"
    )
    record = PaymentRecord(
        session_id=session_id,
        product_id=product_id,
        status="pending",
        url=url,
        token=token,
        created_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    store.payments[key] = record
    _save_store(path, store)
    return url


def confirm_payment(session_id: str, product_id: str) -> PaymentStatus:
    """Mark payment confirmed; idempotent on repeat."""
    path = payments_path()
    store = _load_store(path)
    key = _payment_key(session_id, product_id)
    record = store.payments.get(key)
    if record is None:
        msg = f"no pending payment for session_id={session_id}, product_id={product_id}"
        raise ValueError(msg)

    if record.status == "confirmed":
        return "confirmed"

    record.status = "confirmed"
    record.confirmed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    store.payments[key] = record
    _save_store(path, store)
    return "confirmed"
