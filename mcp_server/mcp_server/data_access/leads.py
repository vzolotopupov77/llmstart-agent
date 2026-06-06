"""Lead persistence to data/leads.txt."""

import json
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from mcp_server.paths import leads_path


class LeadRecord(BaseModel):
    """Lead fields persisted as JSON Lines."""

    email: EmailStr
    phone: str = Field(min_length=1)
    name: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    channel: Literal["web", "telegram"]
    segment: Literal["b2b", "b2c"]
    ts: str | None = None

    def to_json_line(self) -> str:
        """Serialize lead with timestamp."""
        payload = self.model_dump()
        payload["ts"] = self.ts or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return json.dumps(payload, ensure_ascii=False)


def append_lead(lead: LeadRecord) -> None:
    """Append one JSON line to leads.txt without logging PII."""
    path = leads_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = lead.to_json_line()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
