from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Mapping
from fastapi import FastAPI, HTTPException, status
from opentelemetry import trace

from app.core.tracing import init_tracing, get_tracer
from app.api.schemas import IngestDocument
from app.core.kuzu import ensure_database, get_conn
from app.graph.read import list_chunks
from app.graph.schema import ensure_schema, ensure_vector_schema
from app.graph.seed import _as_qr, seed_sample
from app.graph.repo import document_exists, create_document, create_section, create_chunk
from app.graph.search import search_chunks


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database()
    ensure_schema()
    ensure_vector_schema()
    yield

app = FastAPI(title="Mini Graph-RAG (TerminusDB)", lifespan=lifespan)
init_tracing(app)
tracer = get_tracer(__name__)


@app.get("/health")
async def health() -> dict[str, str]:
    with tracer.start_as_current_span("health"):
        span = trace.get_current_span()
        span.set_attribute("health.ok", True)
        return {"status": "ok"}


@app.post("/seed")
def seed(reset: bool = True):
    """
    Seeds the DB with a small sample graph and returns verification counts.
    Use `reset=false` to keep existing data.
    """
    return seed_sample(reset=reset)


@app.get("/chunks")
def get_chunks(limit: int = 100, doc: str | None = None):
    """
    List chunks with their section & document.
    Optional: filter by document title via ?doc=Sample%20Doc
    """
    items = list_chunks(limit=limit, doc_title=doc)
    return {"count": len(items), "items": items}


@app.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest(doc: IngestDocument):
    """
    Create a new Document with Sections/Chunks.
    If a Document with the same title exists -> 409 Conflict (no changes).
    Section/chunk order is taken from the input list order.
    """
    if document_exists(doc.title):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document with title '{doc.title}' already exists",
        )

    doc_id = create_document(doc.title)
    section_ids: list[int] = []
    chunk_ids: list[int] = []

    for i, sec in enumerate(doc.sections):
        sid = create_section(doc_id, sec.title, i)
        section_ids.append(sid)
        for j, text in enumerate(sec.chunks):
            cid = create_chunk(sid, text, j)
            chunk_ids.append(cid)

    return {
        "document_id": doc_id,
        "section_ids": section_ids,
        "chunk_ids": chunk_ids,
        "sections_created": len(section_ids),
        "chunks_created": len(chunk_ids),
    }


@app.get("/search")
def search(q: str, doc: str | None = None, limit: int = 20, ci: bool = True):
    """
    Case-insensitive substring search in Chunk.text by default (ci=true).
    Pass ci=false for case-sensitive search.
    Optional: restrict to a document via ?doc=Title
    """
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required",
        )
    items = search_chunks(q=q, doc_title=doc, limit=limit, case_insensitive=ci)
    return {"count": len(items), "items": items}


@app.get("/debug/indexes")
def debug_indexes():
    """
    Show existing indexes.
    """
    res = _as_qr(get_conn().execute("CALL SHOW_INDEXES() RETURN *"))
    out = []
    while res.has_next():
        row = res.get_next()
        if isinstance(row, Mapping):
            out.append(dict(row))
        else:
            out.append({
                "table name": row[0],
                "index name": row[1],
                "index type": row[2],
                "property names": row[3],
                "extension loaded": row[4],
                "index definition": row[5],
            })
    return {"indexes": out}
