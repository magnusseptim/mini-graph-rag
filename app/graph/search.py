from __future__ import annotations
import re
from typing import Any, Mapping, Sequence, cast
from app.core.kuzu import get_conn
from app.graph.seed import _as_qr


def _pattern(q: str, ci: bool) -> str:
    # Safe substring pattern; (?i) enables case-insensitive when requested
    core = re.escape(q)
    return (f"(?i).*{core}.*") if ci else (f".*{core}.*")


def search_chunks(
    q: str,
    doc_title: str | None = None,
    limit: int = 20,
    case_insensitive: bool = True,
) -> list[dict[str, Any]]:
    """
    Search chunks by text, optionally filtering by document title.
    Case-insensitive substring match.
    Returns a list of dicts with document, section, chunk info.
    """
    if limit <= 0:
        limit = 20

    params: dict[str, Any] = {
        "pat": _pattern(q, case_insensitive),
        "lim": int(limit),
    }

    where_parts = ["c.text =~ $pat"]
    if doc_title:
        where_parts.append("d.title = $t")
        params["t"] = doc_title

    where = "WHERE " + " AND ".join(where_parts)

    qtext = f"""
    MATCH (d:Document)-[:ContainsDocSection]->(s:Section)-[:ContainsSectionChunk]->(c:Chunk)
    {where}
    RETURN
        d.id    AS document_id,
        d.title AS document,
        s.id    AS section_id,
        s.title AS section,
        c.id    AS chunk_id,
        c.ord   AS chunk_ord,
        c.text  AS chunk
    ORDER BY d.id, s.ord, c.ord
    LIMIT $lim
    """

    res = _as_qr(get_conn().execute(qtext, params))
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
            })
        else:
            seq = cast(Sequence[Any], row)
            out.append({
                "document_id":   seq[0],
                "document":      seq[1],
                "section_id":    seq[2],
                "section":       seq[3],
                "chunk_id":      seq[4],
                "chunk_ord":     seq[5],
                "text":          seq[6],
            })
    return out
