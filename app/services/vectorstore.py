from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import settings
from app.core.logging import logger
from app.services.embedder import get_embeddings


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=settings.chroma_collection,
        embedding_function=get_embeddings(),
        client_settings=_chroma_client_settings(),
    )


def _chroma_client_settings():
    import chromadb

    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )


def index_chunks(
    chunks: list[str],
    doc_id: str,
    filename: str,
) -> int:
    """Embed and store document chunks. Returns number of chunks stored."""
    vs = get_vectorstore()
    docs = [
        Document(
            page_content=chunk,
            metadata={"doc_id": doc_id, "filename": filename, "chunk_index": i},
        )
        for i, chunk in enumerate(chunks)
    ]
    ids = [f"{doc_id}_{i}" for i in range(len(docs))]
    vs.add_documents(docs, ids=ids)
    logger.info("chunks_indexed", doc_id=doc_id, count=len(docs))
    return len(docs)


def similarity_search(
    question: str,
    top_k: int,
) -> list[tuple[Document, float]]:
    """Return top-k documents with relevance scores."""
    vs = get_vectorstore()
    return vs.similarity_search_with_relevance_scores(question, k=top_k)


def list_documents() -> list[dict]:
    """Return deduplicated list of indexed documents."""
    vs = get_vectorstore()
    col = vs._collection
    results = col.get(include=["metadatas"])
    seen: dict[str, dict] = {}
    for meta in results["metadatas"]:
        doc_id = meta.get("doc_id", "unknown")
        if doc_id not in seen:
            seen[doc_id] = {"doc_id": doc_id, "filename": meta.get("filename", ""), "chunks": 0}
        seen[doc_id]["chunks"] += 1
    return list(seen.values())


def delete_document(doc_id: str) -> int:
    """Delete all chunks for a document. Returns chunks removed."""
    vs = get_vectorstore()
    col = vs._collection
    results = col.get(where={"doc_id": doc_id}, include=["metadatas"])
    ids = results.get("ids", [])
    if ids:
        col.delete(ids=ids)
    logger.info("document_deleted", doc_id=doc_id, chunks_removed=len(ids))
    return len(ids)
