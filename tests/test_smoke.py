# tests/test_smoke.py
from __future__ import annotations
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_seed_idempotent(client: TestClient):
    # fresh seed
    r1 = client.post("/seed", params={"reset": True})
    assert r1.status_code == 200
    body = r1.json()
    assert body["created"] is True
    t = body["totals"]
    assert t["documents"] == 1
    assert t["sections"] == 2
    assert t["chunks"] == 3
    assert t["doc_to_section_edges"] == 2
    assert t["section_to_chunk_edges"] == 3
    assert len(body["sample"]) == 3

    # idempotent re-run (no duplicates)
    r2 = client.post("/seed", params={"reset": False})
    assert r2.status_code == 200
    assert r2.json()["created"] is False


def test_ingest_conflict(client: TestClient):
    # Start from a clean DB for this test
    client.post("/seed", params={"reset": True})

    payload = {
        "title": "Kickoff Notes",
        "sections": [
            {"title": "Intro", "chunks": ["hi", "agenda"]},
            {"title": "Body",  "chunks": ["topic A", "topic B", "Q&A"]},
        ],
    }

    r1 = client.post("/ingest", json=payload)
    assert r1.status_code == 201
    created = r1.json()
    assert created["sections_created"] == 2
    assert created["chunks_created"] == 5

    # Same title again -> 409 conflict
    r2 = client.post("/ingest", json=payload)
    assert r2.status_code == 409

    # Verify listing matches 5 chunks
    r3 = client.get("/chunks", params={"doc": "Kickoff Notes"})
    assert r3.status_code == 200
    data = r3.json()
    assert data["count"] == 5


def test_search_substring(client):
    # clean DB, then ingest a known doc
    client.post("/seed", params={"reset": True})
    payload = {
        "title": "Kickoff Notes",
        "sections": [
            {"title": "Intro", "chunks": ["hi", "agenda"]},
            {"title": "Body",  "chunks": ["topic A", "topic B", "Q&A"]},
        ],
    }
    r1 = client.post("/ingest", json=payload)
    assert r1.status_code == 201

    # search "topic" within that document
    r = client.get("/search", params={"q": "topic", "doc": "Kickoff Notes"})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    texts = [item["text"] for item in data["items"]]
    assert "topic A" in texts and "topic B" in texts
