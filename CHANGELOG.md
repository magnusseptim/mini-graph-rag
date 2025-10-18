# Changelog

## v0.1.0 — Mini Graph-RAG MVP
- Embedded **Kùzu** graph (Document → Section → Chunk).
- Endpoints: `/seed`, `/ingest`, `/chunks`, `/search` (CI by default), `/search/semantic` (HNSW + cosine).
- Debug: `/debug/indexes`, `/debug/set_dummy_embeddings` (one-hot demo vectors).
- CI via GitHub Actions + `uv` cache.
- Dockerfile + Make targets (`docker-build`, `docker-run`).
- README Quickstart, API table, troubleshooting.

**Known issue**
- In Docker, `/debug/set_dummy_embeddings` may fail when the vector index is live (works locally). See README.