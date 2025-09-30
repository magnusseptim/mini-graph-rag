from __future__ import annotations
from pathlib import Path
import kuzu
from app.core.config import settings
from app.core.tracing import get_tracer

tracer = get_tracer(__name__)
_db: kuzu.Database | None = None


def get_db() -> kuzu.Database:
    """Get the Kuzu database.

    Returns:
        kuzu.Database: Kuzu database
    """
    global _db
    if _db is None:
        Path(settings.kuzu_db_path).parent.mkdir(parents=True, exist_ok=True)
        _db = kuzu.Database(settings.kuzu_db_path)
    return _db


def get_conn() -> kuzu.Connection:
    """Get a Kuzu connection.

    Returns:
        kuzu.Connection: Kuzu connection
    """
    return kuzu.Connection(get_db())


def ensure_database() -> None:
    """
    Ensure the Kuzu database is created.
    """
    with tracer.start_as_current_span("ensure_database"):
        get_db()