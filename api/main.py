"""Minimal FastAPI app. No agent calls yet."""

from fastapi import FastAPI

app = FastAPI(
    title="Agentic Document Intelligence",
    description="Production-grade document intelligence API",
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    """Health check."""
    return {"status": "ok"}
