"""Structured logging for agents and pipelines. Governance and LLMOps: logs matter."""

from __future__ import annotations

import logging
import sys
from typing import Any

from config import settings


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module/component. Uses app log level from settings."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger


def log_agent_step(
    logger: logging.Logger,
    agent: str,
    step: str,
    decision: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> None:
    """Log one agent decision step. Use for audit and LLMOps."""
    msg = f"agent_step | agent={agent} | step={step}"
    if trace_id is not None:
        msg += f" | trace_id={trace_id}"
    if decision is not None:
        msg += f" | decision={decision!r}"
    logger.info(msg)
