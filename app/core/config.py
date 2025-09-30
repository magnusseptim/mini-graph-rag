from __future__ import annotations
from pydantic import BaseModel, StrictStr, AnyHttpUrl
import os


class Settings(BaseModel):
    service_name: StrictStr = "mini-graph-rag"

    otlp_endpoint: StrictStr | None = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    kuzu_db_path: StrictStr = os.getenv(
        "KUZU_DB_PATH", "./var/mini-graph-rag.kuzu")

    ollama_url: AnyHttpUrl | StrictStr = os.getenv(
        "OLLAMA_URL", "http://localhost:11434"
    )


settings = Settings()
