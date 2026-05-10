from functools import lru_cache
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import settings
from app.core.logging import logger


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Load embedding model once and cache it for the process lifetime."""
    logger.info("loading_embedding_model", model=settings.embed_model)
    embeddings = HuggingFaceEmbeddings(
        model_name=settings.embed_model,
        model_kwargs={"device": "mps"},   # Apple Silicon GPU
        encode_kwargs={"normalize_embeddings": True},
    )
    logger.info("embedding_model_ready", model=settings.embed_model)
    return embeddings
