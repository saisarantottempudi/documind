# ── Stage 1: dependency builder ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install all runtime deps into /install so the runtime stage stays slim
COPY pyproject.toml .
RUN pip install --upgrade pip --quiet && \
    pip install --prefix=/install --quiet \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.32.0" \
        "pydantic>=2.10.0" \
        "pydantic-settings>=2.7.0" \
        "langchain>=0.3.0" \
        "langchain-community>=0.3.0" \
        "langchain-text-splitters>=0.3.0" \
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

# NOTE: The embedding model (all-MiniLM-L6-v2) is downloaded at first startup
# via TRANSFORMERS_CACHE / sentence-transformers cache on the mounted volume.
# This keeps the image lean (~800 MB vs ~1.5 GB with the model baked in)
# and avoids the 100 MB network download during every CI build.

USER documind

EXPOSE 8000

ENV TRANSFORMERS_CACHE=/tmp/hf_cache \
    HF_HOME=/tmp/hf_cache

ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", \
            "--host", "0.0.0.0", "--port", "8000", \
            "--workers", "2", "--loop", "uvloop"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/liveness')"
