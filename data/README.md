# Data layout

- **raw_docs/** — Original documents before ingestion (PDFs, text, etc.). Pipelines read from here.
- **processed_chunks/** — Chunked + embedded outputs (if persisted to disk). Embedding pipeline can be restart-safe using this.
- **eval_sets/** — Small evaluation datasets (e.g. question/answer pairs) for RAG evaluation scripts. Metrics saved as JSON elsewhere; this holds inputs.

Vector store (Chroma) path is configured via `VECTOR_STORE_PATH` in config (default `./data/chroma`).
