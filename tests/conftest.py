from __future__ import annotations
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def client(tmp_path_factory) -> TestClient:
    db_dir = tmp_path_factory.mktemp("kuzu-db")
    os.environ["KUZU_DB_PATH"] = str(db_dir / "test.kuzu")

    from app.core.kuzu import ensure_database
    from app.graph.schema import ensure_schema
    ensure_database()
    ensure_schema()

    from app.api.routes import app
    return TestClient(app)
