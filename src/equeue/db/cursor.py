#src/equeue/db/cursor.py

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID



@dataclass(frozen=True)
class Cursor:
    created_at: datetime
    id: UUID


def encode_cursor(created_at: datetime, id: UUID) -> str:
    payload = {"created_at": created_at.isoformat(), "id": str(id)}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")

def decode_cursor(cursor: str) -> Cursor:
    raw = base64.urlsafe_b64decode(cursor.encode("ascii"))
    payload = json.loads(raw.decode("utf-8"))
    return Cursor(
        created_at=datetime.fromisoformat(payload["created_at"]),
        id=UUID(payload["id"]),
    )