# Changelog

## v0.1.0 — Mini Graph-RAG MVP
- Embedded **Kùzu** graph (Document → Section → Chunk).
- Endpoints: `/seed`, `/ingest`, `/chunks`, `/search` (CI by default), `/search/semantic` (HNSW + cosine).
- Debug: `/debug/indexes`, `/debug/set_dummy_embeddings` (one-hot demo vectors).
- CI via GitHub Actions + `uv` cache.
- Dockerfile + Make targets (`docker-build`, `docker-run`).
- README Quickstart, API table, troubleshooting.

### Known issue / workaround
- If `/debug/set_dummy_embeddings` fails with:
  `Cannot set property vec in table embeddings … used in one or more indexes`, you likely have a **stale local DB** with an old vector index. Run `make clean-db`, then `make seed` → `make seed-emb`. The index is created after embeddings are written.