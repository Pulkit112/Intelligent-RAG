"""Agent business orchestration. API calls this; it delegates to agents/ and tools/. No logic in API."""

from __future__ import annotations

from typing import Any


class AgentService:
    """Orchestrates role-based agents (retrieval, validation, report, QA). Thin layer over agents/."""

    def __init__(self) -> None:
        """Initialize with agent instances (injected later)."""
        pass

    def run_retrieval(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run retrieval agent. Stub for now."""
        return {"results": [], "decision": {}}

    def run_validation(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run validation agent. Stub for now."""
        return {"valid": True, "issues": []}

    def run_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Run report agent. Stub for now."""
        return {"report": ""}

    def run_qa(self, question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run QA agent. Stub for now."""
        return {"answer": "", "citations": []}
