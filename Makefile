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

# Debug Vector Indexes
indexes:
	curl -s "http://127.0.0.1:8000/debug/indexes" | jq

# call the debug helper to populate deterministic embeddings
seed-emb:
	curl -s -X POST "http://127.0.0.1:8000/debug/set_dummy_embeddings" | jq

# run a simple semantic search with a one-hot query vector (index 0)
semantic:
	uv run python -c "import json,urllib.request; vec=[0.0]*384; vec[0]=1.0; req=urllib.request.Request('http://127.0.0.1:8000/search/semantic', data=json.dumps({'vector':vec,'k':3,'efs':200}).encode(), headers={'Content-Type':'application/json'}, method='POST'); print(urllib.request.urlopen(req).read().decode())"

# Run tests via uv (matches CI)
test:
	uv run pytest -q

# Nuke local DB artifacts if something gets stuck
clean-db:
	rm -f var/*.kuzu var/*.kuzulog var/*.kuzu.wal var/*.kuzu.tmp

# Alias for CI locally
ci: test