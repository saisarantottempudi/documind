import hashlib
import json

import redis

from app.core.config import settings
from app.core.logging import logger


def _get_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def _cache_key(question: str, top_k: int) -> str:
    payload = f"{question.strip().lower()}:{top_k}"
    return "documind:query:" + hashlib.sha256(payload.encode()).hexdigest()


def get_cached(question: str, top_k: int) -> dict | None:
    try:
        client = _get_client()
        raw = client.get(_cache_key(question, top_k))
        if raw:
            logger.info("cache_hit", question=question[:60])
            return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get_failed", error=str(exc))
    return None


def set_cached(question: str, top_k: int, data: dict) -> None:
    try:
        client = _get_client()
        client.setex(
            _cache_key(question, top_k),
            settings.cache_ttl_seconds,
            json.dumps(data),
        )
    except Exception as exc:
        logger.warning("cache_set_failed", error=str(exc))
