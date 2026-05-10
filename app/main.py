from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.routes import documents, query, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("documind_starting", env=settings.app_env, model=settings.ollama_model)
    # Pre-load embedding model on startup so first request is not slow
    from app.services.embedder import get_embeddings
    get_embeddings()
    logger.info("documind_ready")
    yield
    logger.info("documind_shutdown")


app = FastAPI(
    title="DocuMind",
    description="Enterprise AI Document Intelligence — RAG with Chain-of-Thought",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(query.router)
