from fastapi.testclient import TestClient


def test_vector_index_visible(client: TestClient):
    r = client.get("/debug/indexes")
    assert r.status_code == 200
    data = r.json()
    assert "indexes" in data and isinstance(data["indexes"], list)
    # Expect our HNSW index on Chunk.embedding
    assert any(
        (idx.get("table name") == "Chunk" and idx.get("index name") == "chunk_embedding_idx")
        for idx in data["indexes"]
    )
