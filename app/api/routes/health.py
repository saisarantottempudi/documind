import httpx
import redis
from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


async def _check_ollama() -> str:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            return "ok" if r.status_code == 200 else f"http_{r.status_code}"
    except Exception:
        return "unreachable"


def _check_redis() -> str:
    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        return "ok" if client.ping() else "failed"
    except Exception:
        return "unreachable"


def _check_chromadb() -> str:
    try:
        import chromadb

        c = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        c.heartbeat()
        return "ok"
    except Exception:
        return "unreachable"


@router.get("/health", response_model=HealthResponse)
async def health():
    """Liveness + dependency health check."""
    ollama_status = await _check_ollama()
    return HealthResponse(
        status="ok",
        ollama=ollama_status,
        chromadb=_check_chromadb(),
        redis=_check_redis(),
    )


@router.get("/readiness")
async def readiness():
    """Kubernetes readiness probe — returns 200 only when all deps are up."""
    ollama = await _check_ollama()
    chroma = _check_chromadb()
    red = _check_redis()
    if "ok" in (ollama, chroma, red) and all(s == "ok" for s in (ollama, chroma, red)):
        return {"status": "ready"}
    return {"status": "not_ready", "ollama": ollama, "chromadb": chroma, "redis": red}


@router.get("/liveness")
async def liveness():
    """Kubernetes liveness probe — always 200 if process is alive."""
    return {"status": "alive"}
