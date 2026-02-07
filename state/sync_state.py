"""Per-source sync state: last_checksum, last_processed_at, status. JSON under data/state/."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STATE_DIR = Path("data/state")
STATE_FILE = STATE_DIR / "sync_state.json"


@dataclass
class SyncStateRecord:
    """Per-source progress for restart-safe ingestion."""

    source_uri: str
    last_checksum: str | None
    last_processed_at: datetime | None
    status: str  # e.g. "processed", "failed", "pending"


def _ensure_state_dir() -> Path:
    """Ensure data/state exists; return STATE_DIR."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def _serialize_dt(dt: datetime | None) -> str | None:
    """Serialize datetime to ISO string."""
    return dt.isoformat() if dt else None


def _deserialize_dt(s: str | None) -> datetime | None:
    """Deserialize ISO string to datetime."""
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_sync_state(path: Path | None = None) -> dict[str, SyncStateRecord]:
    """Load sync state from JSON; return dict source_uri -> SyncStateRecord."""
    p = path if path is not None else STATE_FILE
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    result: dict[str, SyncStateRecord] = {}
    for uri, rec in data.items():
        if isinstance(rec, dict):
            result[uri] = SyncStateRecord(
                source_uri=uri,
                last_checksum=rec.get("last_checksum"),
                last_processed_at=_deserialize_dt(rec.get("last_processed_at")),
                status=rec.get("status", "pending"),
            )
    return result


def save_sync_state(state: dict[str, SyncStateRecord], path: Path | None = None) -> None:
    """Persist sync state to JSON."""
    _ensure_state_dir()
    p = path if path is not None else STATE_FILE
    data = {
        uri: {
            "source_uri": r.source_uri,
            "last_checksum": r.last_checksum,
            "last_processed_at": _serialize_dt(r.last_processed_at),
            "status": r.status,
        }
        for uri, r in state.items()
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_sync_state(
    source_uri: str,
    last_checksum: str | None = None,
    last_processed_at: datetime | None = None,
    status: str | None = None,
    path: Path | None = None,
) -> None:
    """Update one source's record and save. Load, update, save."""
    state = load_sync_state(path)
    rec = state.get(
        source_uri,
        SyncStateRecord(source_uri=source_uri, last_checksum=None, last_processed_at=None, status="pending"),
    )
    rec = SyncStateRecord(
        source_uri=rec.source_uri,
        last_checksum=last_checksum if last_checksum is not None else rec.last_checksum,
        last_processed_at=last_processed_at if last_processed_at is not None else rec.last_processed_at,
        status=status if status is not None else rec.status,
    )
    state[source_uri] = rec
    save_sync_state(state, path)
