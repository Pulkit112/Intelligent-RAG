"""Download and cache BGE-M3 model locally. Run once before tests to avoid download during pytest."""

from __future__ import annotations

import sys


def main() -> int:
    print("Downloading/loading BAAI/bge-m3 (saved to HuggingFace cache)...", flush=True)
    try:
        from embeddings.bge_m3_embedder import BgeM3Embedder
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    embedder = BgeM3Embedder(model_name="BAAI/bge-m3", batch_size=4, normalize=True, device=None)
    print(f"Model loaded. Device: {embedder._device}. Vector dim: {embedder.vector_dim}", flush=True)
    embedder.embed_texts(["warmup"])
    print("Done. Model is cached. You can run pytest now.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
