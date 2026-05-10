import pytest
from unittest.mock import patch, MagicMock


@patch("app.services.rag.vectorstore.index_chunks", return_value=3)
def test_ingest_plain_text(mock_index):
    from app.services.rag import ingest_document
    content = b"This is a plain text document with enough content to chunk properly." * 10
    result = ingest_document(content, "sample.txt", "text/plain")
    assert result.filename == "sample.txt"
    assert result.chunks_indexed == 3
    mock_index.assert_called_once()


@patch("app.services.rag.vectorstore.index_chunks", return_value=0)
def test_ingest_empty_document_raises(mock_index):
    from app.services.rag import ingest_document
    with pytest.raises(ValueError, match="no text chunks"):
        ingest_document(b"", "empty.txt", "text/plain")
