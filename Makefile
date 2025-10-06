.PHONY: run seed chunks ingest test clean-db ci

# Dev server (ignore DB changes so reload doesn’t thrash)
run:
	uv run uvicorn app.api.routes:app --reload --reload-exclude var/* --port 8000

# Seed sample data (fresh)
seed:
	curl -s -X POST "http://127.0.0.1:8000/seed?reset=true" | jq

# List chunks (all)
chunks:
	curl -s "http://127.0.0.1:8000/chunks" | jq

# Quick ingest demo
ingest:
	curl -s -X POST http://127.0.0.1:8000/ingest \
	  -H "Content-Type: application/json" \
	  -d '{"title":"Kickoff Notes","sections":[{"title":"Intro","chunks":["hi","agenda"]},{"title":"Body","chunks":["topic A","topic B","Q&A"]}]}' | jq

# Run tests via uv (matches CI)
test:
	uv run pytest -q

# Nuke local DB artifacts if something gets stuck
clean-db:
	rm -f var/*.kuzu var/*.kuzulog var/*.kuzu.wal var/*.kuzu.tmp

# Alias for CI locally
ci: test