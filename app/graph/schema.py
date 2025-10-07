from __future__ import annotations
from typing import Sequence, Mapping
from app.core.kuzu import get_conn
from app.core.tracing import get_tracer
from app.graph.seed import _as_qr

tracer = get_tracer(__name__)


def _ensure_vector_loaded() -> None:
    conn = get_conn()
    for stmt in ("INSTALL VECTOR;", "LOAD VECTOR;"):
        try:
            conn.execute(stmt)
        except Exception as e:
            # simplest acceptable guard: only ignore “already …” cases
            if "already" in str(e).lower():
                continue
            raise


DDL = [

    # Nodes
    """
    CREATE NODE TABLE IF NOT EXISTS Document(
        id SERIAL PRIMARY KEY,
        title STRING
    );
    """,
    """
    CREATE NODE TABLE IF NOT EXISTS Section(
        id SERIAL PRIMARY KEY,
        title STRING,
        ord INT32
    );
    """,
    """
    CREATE NODE TABLE IF NOT EXISTS Chunk(
        id SERIAL PRIMARY KEY,
        text STRING,
        ord INT32,
        embedding FLOAT[384]
    );
    """,

    # Relationships (directional)
    "CREATE REL TABLE IF NOT EXISTS ContainsDocSection(FROM Document TO Section, ONE_MANY);",
    "CREATE REL TABLE IF NOT EXISTS ContainsSectionChunk(FROM Section TO Chunk, ONE_MANY);",
    "CREATE REL TABLE IF NOT EXISTS NextChunk(FROM Chunk TO Chunk, MANY_ONE);",
]


def ensure_schema() -> None:
    """
    Ensure the database schema is there and up to date. Confirm index exists.
    """
    with tracer.start_as_current_span("kuzu.ensure_schema"):
        conn = get_conn()

        _ensure_vector_loaded()

        for stmt in DDL:
            try:
                conn.execute(stmt)
            except Exception as e:
                msg = str(e).lower()
                if "already exists" in msg or "is already installed" in msg:
                    continue
                raise

        try:
            conn.execute(
                "CALL CREATE_VECTOR_INDEX('Chunk','chunk_embedding_idx','embedding', metric := 'cosine');"
                )
        except Exception:
            pass  # index already exists


def ensure_vector_schema() -> None:
    """
    Add Chunk.embedding and create vector index if missing.
    """
    conn = get_conn()
    _ensure_vector_loaded()

    conn.execute("ALTER TABLE Chunk ADD IF NOT EXISTS embedding FLOAT[384];")

    idx_name = "chunk_embedding_idx"
    res = _as_qr(conn.execute("CALL SHOW_INDEXES() RETURN *"))

    exist = False
    while res.has_next():
        row = res.get_next()
        if isinstance(row, Mapping):
            table = row["table name"]
            name = row["index name"]
        else:
            seq = row if isinstance(row, Sequence) else []
            table = seq[0] if len(seq) > 0 else None
            name = seq[1] if len(seq) > 1 else None
        if str(table).lower() == "chunk" and str(name).lower() == idx_name:
            exist = True
            break

    if not exist:
        conn.execute(
            "CALL CREATE_VECTOR_INDEX('Chunk','chunk_embedding_idx','embedding', metric := 'cosine');"
        )
