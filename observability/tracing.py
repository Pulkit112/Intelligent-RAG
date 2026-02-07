"""Lightweight tracing context for request/run correlation. Agent logs can attach trace_id."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str | None:
    """Return current request/run trace id, or None if not set."""
    return _trace_id.get()


def set_trace_id(trace_id: str | None = None) -> str | None:
    """Set trace id for current context. If None, generate a new UUID. Returns the id."""
    value = trace_id or str(uuid.uuid4())
    _trace_id.set(value)
    return value


def clear_trace_id() -> None:
    """Clear trace id for current context."""
    _trace_id.set(None)
