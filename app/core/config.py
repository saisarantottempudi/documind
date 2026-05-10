from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "info"

    # LLM
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"

    # Embeddings
    embed_model: str = "all-MiniLM-L6-v2"

    # ChromaDB
    chroma_host: str = "chromadb"
    chroma_port: int = 8001
    chroma_collection: str = "documind"

    # Redis
    redis_url: str = "redis://redis:6379"
    cache_ttl_seconds: int = 300

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k: int = 5

    # Upload
    max_upload_size_mb: int = 50


settings = Settings()
