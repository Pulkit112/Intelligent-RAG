"""Text normalization for PDF and other extracted text. Run before chunking to improve embedding and search."""

from __future__ import annotations

import unicodedata

# PDF ligatures and common Unicode substitutes -> ASCII
LIGATURE_MAP: list[tuple[str, str]] = [
    ("\uFB01", "fi"),   # ﬁ
    ("\uFB02", "fl"),   # ﬂ
    ("\uFB03", "ffi"),  # ﬃ
    ("\uFB04", "ffl"),  # ﬄ
    ("\uFB00", "ff"),   # ﬀ
    ("\u2018", "'"),    # left single quote
    ("\u2019", "'"),    # right single quote
    ("\u201C", '"'),    # left double quote
    ("\u201D", '"'),    # right double quote
    ("\u2013", "-"),    # en dash
    ("\u2014", "-"),   # em dash
]


def normalize_ligatures(text: str) -> str:
    """
    Replace PDF/Unicode ligatures with ASCII equivalents (e.g. ﬁ -> fi, ﬂ -> fl).

    Reduces embedding noise and improves search matching.
    """
    for lig, replacement in LIGATURE_MAP:
        text = text.replace(lig, replacement)
    return text


def normalize_text(text: str) -> str:
    """
    Normalize text for chunking: Unicode NFC then ligature replacement.

    Run after extraction and before chunking. Improves embedding quality,
    search matching, and eval metrics.
    """
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    text = normalize_ligatures(text)
    return text
