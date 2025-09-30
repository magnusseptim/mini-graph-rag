from __future__ import annotations
from app.core.kuzu import get_conn
from app.graph.seed import _as_qr, _first_scalar, _single_int


def document_exists(title: str) -> bool:
    """Check if a document with the given title exists in the database.

    Args:
        title (str): The title of the document to check.

    Returns:
        bool: True if the document exists, False otherwise.
    """
    cnt = _single_int("MATCH (d:Document {title: $t}) RETURN COUNT(d) AS cnt", {"t": title})
    return cnt > 0


def create_document(title: str) -> int:
    """Create a new document with the given title.

    Args:
        title (str): The title of the document to create.
    """
    q = "CREATE (d:Document {title: $t}) RETURN d.id AS id"
    res = _as_qr(get_conn().execute(q, {"t": title}))
    val = _first_scalar(res)
    assert val is not None, "Failed to create document"
    return int(val)


def create_section(doc_id: int, title: str, ord_: int) -> int:
    """Create a new section with the given title and link it to the specified document.

    Args:
        doc_id (int): The ID of the document to link the section to.
        title (str): The title of the section to create.
        ord_ (int): The order of the section within the document.

    Returns:
        int: The ID of the created section.
    """
    q = """
    MATCH (d:Document {id:$doc})
        CREATE (s:Section {title:$title, ord:$ord }),
        (d)-[:ContainsDocSection]-> (s)
    RETURN s.id AS id
    """
    res = _as_qr(get_conn().execute(q, {"doc": doc_id, "title": title, "ord": int(ord_)}))
    val = _first_scalar(res)
    assert val is not None, "Failed to create section"
    return int(val)


def create_chunk(section_id: int, text: str, ord_: int) -> int:
    """
    Create a new chunk with the given text and link it to the specified section.
    Args:
        section_id (int): The ID of the section to link the chunk to.
        text (str): The text of the chunk to create.
        ord_ (int): The order of the chunk within the section.
    Returns:
        int: The ID of the created chunk.
    """
    q = """
    MATCH (s:Section {id:$sid})
    CREATE (c:Chunk {text:$text, ord:$ord}),
           (s)-[:ContainsSectionChunk]->(c)
    RETURN c.id AS id
    """
    res = _as_qr(get_conn().execute(q, {"sid": section_id, "text": text, "ord": int(ord_)}))
    val = _first_scalar(res)
    assert val is not None, "Failed to create Chunk"
    return int(val)
