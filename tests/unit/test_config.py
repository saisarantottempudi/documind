import os
import pytest
from app.core.config import Settings


def test_defaults():
    s = Settings()
    assert s.ollama_model == "llama3.2:3b"
    assert s.chunk_size == 512
    assert s.chunk_overlap == 64
    assert s.top_k == 5


def test_env_override(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "phi3:mini")
    monkeypatch.setenv("CHUNK_SIZE", "256")
    s = Settings()
    assert s.ollama_model == "phi3:mini"
    assert s.chunk_size == 256
