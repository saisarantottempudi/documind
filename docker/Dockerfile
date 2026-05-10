# ── Stage 1: dependency builder ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies into a prefix so we can copy them cleanly
COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install --prefix=/install hatchling && \
    pip install --prefix=/install \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.32.0" \
        "pydantic>=2.10.0" \
        "pydantic-settings>=2.7.0" \
        "langchain>=0.3.0" \
        "langchain-community>=0.3.0" \
        "langchain-ollama>=0.2.0" \
        "langchain-chroma>=0.1.0" \
        "chromadb>=0.5.0" \
        "sentence-transformers>=3.3.0" \
        "pypdf>=5.1.0" \
        "python-multipart>=0.0.18" \
        "redis>=5.2.0" \
        "prometheus-fastapi-instrumentator>=7.0.0" \
        "structlog>=24.4.0" \
        "httpx>=0.28.0"

# ── Stage 2: runtime ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r documind && useradd -r -g documind -s /sbin/nologin documind

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Pre-download the embedding model so container starts without internet access
# (CI will cache this layer via Docker layer cache)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

USER documind

EXPOSE 8000

# Tini handles PID 1 signal forwarding — use Docker's built-in init
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", \
            "--host", "0.0.0.0", "--port", "8000", \
            "--workers", "2", "--loop", "uvloop"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/liveness')"
