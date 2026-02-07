"""Workflow business orchestration. API calls this; it delegates to graph/. No logic in API."""

from __future__ import annotations

from typing import Any


class WorkflowService:
    """Orchestrates LangGraph workflow runs. Thin layer over graph/; API never touches graph directly."""

    def __init__(self) -> None:
        """Initialize with compiled graph (injected later)."""
        pass

    def run(self, input_state: dict[str, Any], *, max_steps: int = 20) -> dict[str, Any]:
        """Run workflow with given initial state and step guard. Stub for now."""
        return {"final_state": input_state, "steps": 0}

    def run_query_flow(self, query: str) -> dict[str, Any]:
        """Convenience: run full query flow (retrieve -> validate -> report). Stub for now."""
        return self.run({"query": query})
