"""Token count estimation for context packing, retrieval scoring, and agent prompt building."""

from __future__ import annotations

_tiktoken_encoder = None


def _get_encoder():
    """Lazy-load tiktoken encoder (cl100k_base for OpenAI-style models)."""
    global _tiktoken_encoder
    if _tiktoken_encoder is None:
        try:
            import tiktoken
            _tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
        except (ImportError, LookupError):
            pass
    return _tiktoken_encoder


def estimate_token_count(text: str) -> int | None:
    """
    Estimate token count for the given text using tiktoken (cl100k_base).

    Returns None if tiktoken is not installed. Used for context packing,
    retrieval scoring, and agent prompt building.
    """
    if not text:
        return 0
    enc = _get_encoder()
    if enc is None:
        return None
    return len(enc.encode(text))
