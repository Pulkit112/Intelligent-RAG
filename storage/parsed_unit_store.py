"""Optional persistence of ParsedUnits to data/parsed_units/<doc_id>.jsonl."""

from __future__ import annotations

from pathlib import Path

from schemas.parsed_unit import ParsedUnit

PARSED_UNITS_DIR = Path("data/parsed_units")


def persist_parsed_units(doc_id: str, units: list[ParsedUnit], base_dir: Path | None = None) -> Path:
    """
    Write ParsedUnits to data/parsed_units/<doc_id>.jsonl (one JSON object per line).

    Used for: debug extraction quality, retry failed units, evaluate chunking, audit trail.
    """
    directory = base_dir if base_dir is not None else PARSED_UNITS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{doc_id}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for u in units:
            line = u.model_dump_json(mode="json") + "\n"
            f.write(line)
    return path
