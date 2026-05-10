import pytest
from pydantic import ValidationError

from app.models.schemas import QueryRequest, QueryResponse, SourceChunk


def test_query_request_valid():
    req = QueryRequest(question="What is the refund policy?")
    assert req.question == "What is the refund policy?"
    assert req.top_k is None


def test_query_request_custom_top_k():
    req = QueryRequest(question="Explain the onboarding steps", top_k=3)
    assert req.top_k == 3


def test_query_request_too_short():
    with pytest.raises(ValidationError):
        QueryRequest(question="Hi")


def test_query_request_top_k_bounds():
    with pytest.raises(ValidationError):
        QueryRequest(question="Valid question here", top_k=0)
    with pytest.raises(ValidationError):
        QueryRequest(question="Valid question here", top_k=21)


def test_query_response_defaults():
    resp = QueryResponse(question="q", answer="a", sources=[])
    assert resp.cached is False
    assert resp.reasoning_steps == []


def test_source_chunk():
    chunk = SourceChunk(
        doc_id="abc",
        filename="policy.pdf",
        chunk_index=0,
        content="Sample text",
        score=0.87,
    )
    assert chunk.score == 0.87
