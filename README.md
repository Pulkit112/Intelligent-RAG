# Agentic Enterprise Document Intelligence System

Production-grade document intelligence with document ingestion, vector store + embeddings, RAG pipeline with citations, role-based AI agents (retrieval, validation, report, QA), LangGraph workflow orchestration, tool-based agent design, guardrails, evaluation pipeline, and FastAPI serving.

**Tech stack:** Python, LangChain, LangGraph, FastAPI, Chroma, Pydantic, sentence-transformers, OpenAI-compatible LLM APIs.

## Setup (pyenv)

1. **Install Python** (if needed): `pyenv install 3.11`
2. **Set local version:** In project root: `pyenv local 3.11`
3. **Create virtualenv:** `python -m venv .venv`
4. **Activate:** `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
5. **Install:** `pip install -e .` then `pip install -r requirements.txt`
6. **Env:** Copy `.env.example` to `.env` and set `OPENAI_API_KEY` and other variables.

## Run API

From project root (with venv active):

```bash
uvicorn api.main:app --reload
```

Open `http://127.0.0.1:8000/` for health check (`{"status": "ok"}`).

## Run tests

```bash
pytest tests/
```

## Project layout

- `agents/` — Role-based agents (retrieval, validation, report, QA)
- `api/` — FastAPI app, routes, service layer (no business logic; calls services/)
- `config/` — App settings (Pydantic BaseSettings)
- `data/` — `raw_docs/`, `processed_chunks/`, `eval_sets/` (see data/README.md)
- `eval/` — RAG evaluation scripts and metrics
- `graph/` — LangGraph workflow, state, nodes
- `guardrails/` — Schema validation, prompt-injection check, PII masking
- `observability/` — Logger and tracing for agent logs and LLMOps
- `pipelines/` — Document ingestion pipeline
- `prompts/` — Prompt templates (versioned)
- `rag/` — Retriever, prompt builder, generator, citations
- `schemas/` — Shared Pydantic models
- `services/` — Business orchestration (RAG, agent, workflow); API and agents do not mix logic here
- `tools/` — Pure tools called by agents
- `tests/` — Unit and node-level tests
