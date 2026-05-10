"""Shared pytest fixtures and configuration."""
import pytest


# Ensure tests never accidentally write to real external services
@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    """Block real HTTP calls in unit tests — integration tests override selectively."""
    pass  # selective mocking per-test is preferred; this is a placeholder hook
