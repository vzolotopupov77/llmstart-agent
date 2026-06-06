"""save_lead tool handler."""

from typing import Literal

from pydantic import ValidationError

from mcp_server.data_access.leads import LeadRecord, append_lead

Channel = Literal["web", "telegram"]
Segment = Literal["b2b", "b2c"]


def handle_save_lead(
    email: str,
    phone: str,
    name: str,
    product_id: str,
    channel: Channel,
    segment: Segment,
) -> dict[str, bool]:
    """Persist lead to data/leads.txt."""
    try:
        lead = LeadRecord(
            email=email,
            phone=phone,
            name=name,
            product_id=product_id,
            channel=channel,
            segment=segment,
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    append_lead(lead)
    return {"ok": True}
