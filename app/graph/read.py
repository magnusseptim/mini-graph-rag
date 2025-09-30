from __future__ import annotations
from typing import Any, Mapping, Sequence, cast
from app.core.kuzu import get_conn
from app.graph.seed import _as_qr


def list_chunks(limit: int = 100, doc_title: str | None = None) -> list[dict[str, Any]]:
    """
    Return Chunk rows with their Section & Document context.
    Idempotent and safe on empty DB.
    """

    if limit <= 0:
        limit = 100
        
    where = "WHERE d.title = $t" if doc_title else ""
    params: dict[str, Any] = {"t": doc_title} if doc_title else {}
    
    q = f"""
    MATCH (d:Document)-[:ContainsDocSection]->(s:Section)
            -[:ContainsSectionChunk]->(c:Chunk)
    {where}
    RETURN
        d.id   AS document_id,
        d.title AS document,
        s.id   AS section_id,
        s.title AS section,
        c.id   AS chunk_id,
        c.ord  AS chunk_ord,
        c.text AS text
    ORDER BY d.id, s.ord, c.ord
    LIMIT $lim
    """
    params["lim"] = int(limit)

    res = _as_qr(get_conn().execute(q, params))

    out: list[dict[str, Any]] = []
    while res.has_next():
        row = res.get_next()
        if row is None:
            break

        if isinstance(row, Mapping):
            out.append({
                "document_id": row["document_id"],
                "document":    row["document"],
                "section_id":  row["section_id"],
                "section":     row["section"],
                "chunk_id":    row["chunk_id"],
                "chunk_ord":   row["chunk_ord"],
                "text":        row["text"],
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
            })
    return out
