"""Unit-level checkpoint: doc_id + unit_index for restart-at-page-N."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STATE_DIR = Path("data/state")
UNIT_PROGRESS_FILE = STATE_DIR / "unit_progress.json"


@dataclass
class UnitProgressRecord:
    """Per-doc unit progress for restart-at-page-N."""

    doc_id: str
    last_unit_index: int
    last_checksum: str | None
    updated_at: datetime | None


def _ensure_state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def _serialize_dt(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _deserialize_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load_unit_progress(path: Path | None = None) -> dict[str, UnitProgressRecord]:
    """Load unit progress from JSON; return dict doc_id -> UnitProgressRecord."""
    p = path if path is not None else UNIT_PROGRESS_FILE
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    result: dict[str, UnitProgressRecord] = {}
    for doc_id, rec in data.items():
        if isinstance(rec, dict):
            result[doc_id] = UnitProgressRecord(
                doc_id=doc_id,
                last_unit_index=rec.get("last_unit_index", -1),
                last_checksum=rec.get("last_checksum"),
                updated_at=_deserialize_dt(rec.get("updated_at")),
            )
    return result


def save_unit_progress(progress: dict[str, UnitProgressRecord], path: Path | None = None) -> None:
    """Persist unit progress to JSON."""
    _ensure_state_dir()
    p = path if path is not None else UNIT_PROGRESS_FILE
    data = {
        doc_id: {
            "doc_id": r.doc_id,
            "last_unit_index": r.last_unit_index,
            "last_checksum": r.last_checksum,
            "updated_at": _serialize_dt(r.updated_at),
        }
        for doc_id, r in progress.items()
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_unit_progress(
    doc_id: str,
    last_unit_index: int,
    last_checksum: str | None = None,
    path: Path | None = None,
) -> None:
    """Update one doc's unit progress and save."""
    progress = load_unit_progress(path)
    rec = progress.get(
        doc_id,
        UnitProgressRecord(doc_id=doc_id, last_unit_index=-1, last_checksum=None, updated_at=None),
    )
    rec = UnitProgressRecord(
        doc_id=doc_id,
        last_unit_index=last_unit_index,
        last_checksum=last_checksum if last_checksum is not None else rec.last_checksum,
        updated_at=datetime.now(),
    )
    progress[doc_id] = rec
    save_unit_progress(progress, path)
