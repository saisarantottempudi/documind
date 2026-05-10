import json
import pytest
from unittest.mock import MagicMock, patch
from app.services import cache


@patch("app.services.cache._get_client")
def test_cache_miss_returns_none(mock_client):
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_client.return_value = mock_redis

    result = cache.get_cached("some question", top_k=5)
    assert result is None


@patch("app.services.cache._get_client")
def test_cache_hit_returns_dict(mock_client):
    payload = {"question": "q", "answer": "a", "sources": [], "cached": False, "reasoning_steps": []}
    mock_redis = MagicMock()
    mock_redis.get.return_value = json.dumps(payload)
    mock_client.return_value = mock_redis

    result = cache.get_cached("q", top_k=5)
    assert result == payload


@patch("app.services.cache._get_client")
def test_cache_set_calls_setex(mock_client):
    mock_redis = MagicMock()
    mock_client.return_value = mock_redis

    cache.set_cached("question text", 5, {"answer": "test"})
    mock_redis.setex.assert_called_once()


@patch("app.services.cache._get_client")
def test_cache_get_handles_exception_gracefully(mock_client):
    mock_client.side_effect = Exception("redis down")
    # Should not raise — returns None
    result = cache.get_cached("question", 5)
    assert result is None
