from __future__ import annotations
from typing import Any, Mapping, Sequence, cast
from app.core.kuzu import get_conn
from app.graph.seed import _as_qr

DIM: int = 384  # must match FLOAT[384] in Chunk.embedding


def _one_hot(i: int, dim: int = DIM) -> list[float]:
    """Generate a one-hot encoded vector.

    Args:
        i (int): The index to set to 1.
        dim (int, optional): The dimension of the vector. Defaults to DIM.

    Returns:
        list[float]: The one-hot encoded vector.
    """
    v = [0.0] * dim
    v[i % dim] = 1.0
    return v


def semantic_search(
    vector: list[float],
    k: int = 5, efs:
        int = 200,
        doc_title: str | None = None) -> list[dict[str, Any]]:
    """Perform a semantic search over chunks using the provided vector."""

    if len(vector) != DIM:
        raise ValueError(f"vector must be of length {DIM}, got {len(vector)}")

    params: dict[str, Any] = {"vec": vector, "k": int(k), "efs": int(efs)}
    where = ""
    if doc_title is not None:
        where = "WHERE d.title = $t"
        params["t"] = doc_title

    q = f"""
    CALL QUERY_VECTOR_INDEX('Chunk', 'chunk_embedding_idx', $vec, $k, efs := $efs)
    WHICH node AS c, distance
    MATCH (d:Document)-[:ContainsDocSection]->(s:Section)-[:ContainsSectionChunk]->(c)
    {where}
     RETURN
        d.id    AS document_id,
        d.title AS document,
        s.id    AS section_id,
        s.title AS section,
        c.id    AS chunk_id,
        c.ord   AS chunk_ord,
        c.text  AS text,
        distance AS distance
    ORDER BY distance
    LIMIT $k
    """

    res = _as_qr(get_conn().execute(q, params))
    out: list[dict[str, Any]] = []

    while res.has_next():
        row = res.get_next()
        if isinstance(row, Mapping):
            out.append({
                "document_id": row["document_id"],
                "document":    row["document"],
                "section_id":  row["section_id"],
                "section":     row["section"],
                "chunk_id":    row["chunk_id"],
                "chunk_ord":   row["chunk_ord"],
                "text":        row["text"],
                "distance":    row["distance"],
            })
        else:
            seq = cast(Sequence[Any], row)
            out.append({
                "document_id": seq[0],
                "document":    seq[1],
                "section_id":  seq[2],
                "section":     seq[3],
                "chunk_id":    seq[4],
                "chunk_ord":   seq[5],
                "text":        seq[6],
                "distance":    seq[7],
            })

    return out
