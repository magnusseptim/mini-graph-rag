from __future__ import annotations
from typing import Any, Mapping, Sequence, cast

from kuzu import QueryResult
from app.core.kuzu import get_conn

SAMPLE_DOC = "Sample Doc"


def _as_qr(res: QueryResult | list[QueryResult]) -> QueryResult:
    """
    Normalize Connection.execute return into a single QueryResult.
    """
    # If a list ever appears (type stubs / multi-statement), take the first.
    return res[0] if isinstance(res, list) else res


def _first_scalar(res: QueryResult) -> Any:
    """
    Return the first column of the first row, regardless of whether rows are
    sequence-like (tuple/list) or mapping-like (dict/record).
    """
    row = res.get_next()
    if row is None:
        return None
    # Pylance sometimes thinks row is a Mapping[str, Any]
    if isinstance(row, Mapping):
        # take the first column’s value
        return next(iter(row.values()), None)
    # otherwise treat as a positional row (tuple/list)
    seq = cast(Sequence[Any], row)
    return seq[0] if len(seq) else None


def _single_int(query: str, params: dict[str, Any] | None = None) -> int:
    """Execute a query and return a single integer result.

    Args:
        query (str): The query to execute.
        params (dict[str, Any] | None, optional): The parameters for the query. Defaults to None.

    Returns:
        int: The integer result of the query, or 0 if no result is found.
    """
    qres = _as_qr(get_conn().execute(query, params or {}))
    val = _first_scalar(qres)
    return int(val) if val is not None else 0


def _rows(query: str, params: dict[str, Any] | None = None) -> list[tuple]:
    """
    Collect all rows as tuples, tolerating either mapping-like or sequence-like rows.
    Column order for mappings follows projection order.
    """
    qres = _as_qr(get_conn().execute(query, params or {}))
    out: list[tuple] = []
    while qres.has_next():
        row = qres.get_next()
        if row is None:
            break
        if isinstance(row, Mapping):
            out.append(tuple(row.values()))
        else:
            seq = cast(Sequence[Any], row)
            out.append(tuple(seq))
    return out


def seed_sample(reset: bool = True) -> dict[str, Any]:
    conn = get_conn()

    if reset:
        # Remove everything (safe if already empty)
        conn.execute("MATCH (n) DETACH DELETE n;")

    # Create only if our sample doc doesn't exist
    exists = _single_int(
        "MATCH (d:Document {title:$t}) RETURN COUNT(d)",
        {"t": SAMPLE_DOC},
    )

    created = False
    if exists == 0:
        created = True
        # 1 doc, 2 sections, 3 chunks
        conn.execute("CREATE (d:Document {title:$t});", {"t": SAMPLE_DOC})
        conn.execute(
            """
            MATCH (d:Document {title:$t})
            CREATE (s1:Section {title:$s1, ord:0}),
                   (s2:Section {title:$s2, ord:1}),
                   (d)-[:ContainsDocSection]->(s1),
                   (d)-[:ContainsDocSection]->(s2),
                   (s1)-[:ContainsSectionChunk]->(:Chunk {text:$c1, ord:0}),
                   (s2)-[:ContainsSectionChunk]->(:Chunk {text:$c2, ord:0}),
                   (s2)-[:ContainsSectionChunk]->(:Chunk {text:$c3, ord:1});
            """,
            {
                "t": SAMPLE_DOC,
                "s1": "Intro",
                "s2": "Body",
                "c1": "Hello world",
                "c2": "Second chunk",
                "c3": "Third chunk",
            },
        )

    # Verification: counts and a small sample listing
    totals = {
        "documents": _single_int("MATCH (d:Document) RETURN COUNT(d)"),
        "sections": _single_int("MATCH (s:Section) RETURN COUNT(s)"),
        "chunks": _single_int("MATCH (c:Chunk) RETURN COUNT(c)"),
        "doc_to_section_edges": _single_int(
            "MATCH (:Document)-[:ContainsDocSection]->(:Section) RETURN COUNT(*)"
        ),
        "section_to_chunk_edges": _single_int(
            "MATCH (:Section)-[:ContainsSectionChunk]->(:Chunk) RETURN COUNT(*)"
        ),
    }

    sample_rows = _rows(
        """
        MATCH (d:Document {title:$t})-[:ContainsDocSection]->(s:Section)
              -[:ContainsSectionChunk]->(c:Chunk)
        RETURN d.title, s.title, c.ord, c.text
        ORDER BY s.ord, c.ord
        """,
        {"t": SAMPLE_DOC},
    )
    sample = [
        {"document": r[0], "section": r[1], "chunk_ord": r[2], "text": r[3]}
        for r in sample_rows
    ]

    return {"created": created, "totals": totals, "sample": sample}
