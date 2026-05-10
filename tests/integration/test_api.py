"""
Integration tests for the FastAPI app using TestClient.
External services (Ollama, ChromaDB, Redis) are mocked at the service layer
so tests run without any running containers.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# --- Fixtures -----------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    # Patch heavy service initialisations before importing app
    with (
        patch("app.services.embedder.HuggingFaceEmbeddings"),
        patch("app.services.vectorstore.get_vectorstore"),
        patch("app.services.cache._get_client"),
    ):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# --- Health endpoints ---------------------------------------------------

def test_liveness(client):
    r = client.get("/liveness")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_health_returns_200(client):
    with (
        patch("app.api.routes.health._check_ollama", return_value="ok"),
        patch("app.api.routes.health._check_chromadb", return_value="ok"),
        patch("app.api.routes.health._check_redis", return_value="ok"),
    ):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"


# --- Document endpoints ------------------------------------------------

def test_upload_unsupported_type(client):
    r = client.post(
        "/documents/upload",
        files={"file": ("malware.exe", b"binary", "application/octet-stream")},
    )
    assert r.status_code == 415


def test_upload_valid_text(client):
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {
        "doc_id": "abc-123",
        "filename": "policy.txt",
        "chunks_indexed": 5,
        "message": "Successfully indexed 5 chunks.",
    }
    with patch("app.api.routes.documents.rag.ingest_document", return_value=mock_result):
        r = client.post(
            "/documents/upload",
            files={"file": ("policy.txt", b"Some policy content " * 30, "text/plain")},
        )
    assert r.status_code == 201
    assert r.json()["doc_id"] == "abc-123"


def test_list_documents(client):
    with patch("app.api.routes.documents.vectorstore.list_documents", return_value=[
        {"doc_id": "x", "filename": "a.txt", "chunks": 2}
    ]):
        r = client.get("/documents/")
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_delete_document_not_found(client):
    with patch("app.api.routes.documents.vectorstore.delete_document", return_value=0):
        r = client.delete("/documents/nonexistent-id")
    assert r.status_code == 404


# --- Query endpoint ----------------------------------------------------

def test_query_too_short(client):
    r = client.post("/query/", json={"question": "Hi"})
    assert r.status_code == 422


def test_query_success(client):
    from app.models.schemas import QueryResponse
    mock_resp = QueryResponse(
        question="What is the leave policy?",
        answer="Employees get 20 days annual leave.",
        sources=[],
        reasoning_steps=["Step 1: Identified question about leave.", "Step 2: Found answer."],
    )
    with patch("app.api.routes.query.rag.answer_question", return_value=mock_resp):
        r = client.post("/query/", json={"question": "What is the leave policy?"})
    assert r.status_code == 200
    data = r.json()
    assert "20 days" in data["answer"]
    assert len(data["reasoning_steps"]) == 2
