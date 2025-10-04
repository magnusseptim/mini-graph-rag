<p align="center">
  <img src="docs/banner.png" alt="Mini Graph-RAG — Kùzu + FastAPI" width="980">
</p>

# Mini Graph-RAG (Kùzu + FastAPI)

Tiny, teachable Graph-RAG starter that stores a `Document → Section → Chunk` graph in
the embedded **Kùzu** database and exposes simple endpoints for seeding, ingesting,
and listing chunks.

## Why this exists
- **Embedded DB**: no server to run; just `pip/uv` and go.
- **Clean graph shape**: `Document -[:ContainsDocSection]-> Section -[:ContainsSectionChunk]-> Chunk`
- **Idempotent seed** and **safe ingest** (409 on duplicate titles).

## Quickstart

### Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Install & run
```bash
uv sync
uv run uvicorn app.api.routes:app --reload --host 0.0.0.0 --port 8000
```

## Config (env vars)

- KUZU_DB_PATH (default: ./var/mini-graph-rag.kuzu)
- OTEL_EXPORTER_OTLP_ENDPOINT (optional)
- OLLAMA_URL (placeholder for future vectors; unused today)

## API

- **GET** `/health` → {"status":"ok"}
- **POST** `/seed?reset=true|false`
  - Seeds a small sample graph. Idempotent (checks for "Sample Doc").
- **GET** `/chunks?doc=title&limit=100`
  - Lists chunks with their section & document context.
- **POST** `/ingest` (409 on duplicate title).
  - Request body:

```json
{
  "title": "Kickoff Notes",
  "sections": [
    {"title": "Intro", "chunks": ["hi", "agenda"]},
    {"title": "Body",  "chunks": ["topic A", "topic B", "Q&A"]}
  ]
}

```
- **GET** `/search?q=<text>&doc=<title>&limit=20`  
  Case-insensitive substring search in `Chunk.text`. Optional `doc` to restrict to a document.

## Example calls

```bash
# Health
curl -s http://localhost:8000/health

# Seed (fresh)
curl -s -X POST "http://localhost:8000/seed?reset=true" | jq

# List chunks
curl -s "http://localhost:8000/chunks?doc=Sample%20Doc" | jq

# Ingest new doc
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"title":"Kickoff Notes","sections":[
        {"title":"Intro","chunks":["hi","agenda"]},
        {"title":"Body","chunks":["topic A","topic B","Q&A"]}
      ]}' | jq
```

## Project structure (trimmed)

```pgsql
app/
  api/
    routes.py
    schemas.py
  core/
    config.py
    kuzu.py
    tracing.py
  graph/
    schema.py
    seed.py
    search.py
    repo.py
    read.py
var/
  .gitkeep
docs/
tests
  conftest.py
  test_smoke.py

```

## Notes
- Row iteration with Kùzu: use ``` while res.has_next(): row = res.get_next()```.

- ```SERIAL``` IDs keep increasing across deletes—normal.

- Reserved words: avoid ```order```; use ord (or backticks).

## Troubleshooting
**Stuck at “Waiting for application startup.”?**
- Kill stray servers: `ps aux | rg uvicorn` then `kill -9 <pid>`
- Remove local DB artifacts:  
  `rm -f var/*.kuzu var/*.kuzulog var/*.kuzu.wal var/*.kuzu.tmp`
- Start dev server excluding DB dir from reload:  
  `uv run uvicorn app.api.routes:app --reload --reload-exclude var/* --port 8000`

## Roadmap

- /search (text-only), then vectors (embedding column + HNSW index).

- Optional: Dockerize app or use Kùzu Explorer container for browsing.

## License
[MIT](./LICENSE)