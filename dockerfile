# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    # Persist DB outside the image
    KUZU_DB_PATH=/data/mini-graph-rag.kuzu

# System deps that are useful in practice (certs, tz, minimal build tools)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
      ca-certificates tzdata gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip setuptools wheel && pip install .

# Expose FastAPI port
EXPOSE 8000

# Persist DB outside the container
VOLUME ["/data"]

# Healthcheck hits the app /health endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD [ "curl", "-f", "http://localhost:8000/health" ]

# Start the API
CMD ["uvicorn", "app.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]