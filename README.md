<p align="center">
  <img src="docs/banner.png" alt="Mini Graph-RAG — Kùzu + FastAPI" width="980">
</p>

# Mini Graph-RAG (Kùzu + FastAPI)

[![CI](https://github.com/magnusseptim/mini-graph-rag/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/magnusseptim/mini-graph-rag/actions/workflows/ci.yml)


Tiny, teachable Graph-RAG starter that stores a `Document → Section → Chunk` graph in
the embedded **Kùzu** database and exposes simple endpoints for seeding, ingesting,
and listing chunks.

## Why this exists
- **Embedded DB**: no server to run; just `pip/uv` and go.
- **Clean graph shape**: `Document -[:ContainsDocSection]-> Section -[:ContainsSectionChunk]-> Chunk`
- **Idempotent seed** and **safe ingest** (409 on duplicate titles).

## Quickstart

### Make targets
- `make run` — start FastAPI (reload on code; ignores DB dir)
- `make seed` — seed sample data
- `make chunks` — list chunks
- `make ingest` — demo ingest request
- `make indexes` — debug vector indexes
- `make test` — run pytest via uv
- `make clean-db` — delete local Kùzu artifacts (WAL/DB)

### Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Install & run
```bash
uv sync
uv run uvicorn app.api.routes:app --reload --host 0.0.0.0 --port 8000
```

### Dev workflow
```bash
# Install deps (incl. dev)
uv sync --dev

# Run tests (same as CI)
uv run pytest -q

```

## Config (env vars)

- KUZU_DB_PATH (default: ./var/mini-graph-rag.kuzu)
- OTEL_EXPORTER_OTLP_ENDPOINT (optional)
- OLLAMA_URL (placeholder for future vectors; unused today)

## API

| Method | Path                                           | Description |
|-------:|------------------------------------------------|-------------|
| GET    | `/health`                                      | Health check. |
| POST   | `/seed?reset=true\|false`                      | Seed sample data (idempotent if `reset=false`). |
| POST   | `/ingest`                                      | Create a document with sections/chunks. Returns 409 if title exists. |
| GET    | `/chunks?doc=<title>&limit=<n>`                | List chunks (with optional doc filter). |
| GET    | `/search?q=<text>&doc=<title>&limit=<n>&ci=bool` | **Substring search** in `Chunk.text`. `ci=true` (default) is **case-insensitive**; pass `ci=false` for case-sensitive. |
| GET    | `/debug/indexes`                               | lists indexes via `CALL SHOW_INDEXES()`. Quick check locally: `make indexes` |


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

# Case-insensitive (default)
curl -s "http://127.0.0.1:8000/search?q=topic&doc=Kickoff%20Notes" | jq

# Case-sensitive
curl -s "http://127.0.0.1:8000/search?q=TOPIC&doc=Kickoff%20Notes&ci=false" | jq
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
- Remove local DB artifacts (esp. WAL):  
  `rm -f var/*.kuzu var/*.kuzulog var/*.kuzu.wal var/*.kuzu.tmp`
- Start dev server excluding DB directory from reload:  
  `uv run uvicorn app.api.routes:app --reload --reload-exclude var/* --port 8000`

## Roadmap

- Vectors endpoint

- Optional: Dockerize app or use Kùzu Explorer container for browsing.

## License
[MIT](./LICENSE)