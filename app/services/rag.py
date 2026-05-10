import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import QueryResponse, SourceChunk, DocumentUploadResponse
from app.services import vectorstore, cache
from app.services.llm import get_llm, COT_SYSTEM_PROMPT, COT_HUMAN_TEMPLATE, parse_cot_response


def _build_chain():
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(COT_SYSTEM_PROMPT),
        HumanMessagePromptTemplate.from_template(COT_HUMAN_TEMPLATE),
    ])
    return (
        {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
        | prompt
        | get_llm()
        | StrOutputParser()
    )


def ingest_document(content: bytes, filename: str, mime: str) -> DocumentUploadResponse:
    """Parse, chunk, embed, and index a document. Returns upload metadata."""
    text = _extract_text(content, filename, mime)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_text(text)
    if not chunks:
        raise ValueError("Document produced no text chunks after parsing.")

    doc_id = str(uuid.uuid4())
    count = vectorstore.index_chunks(chunks, doc_id=doc_id, filename=filename)
    logger.info("document_ingested", filename=filename, doc_id=doc_id, chunks=count)
    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=filename,
        chunks_indexed=count,
        message=f"Successfully indexed {count} chunks.",
    )


def answer_question(question: str, top_k: int) -> QueryResponse:
    """Retrieve relevant chunks and generate a chain-of-thought answer."""
    # Check cache first
    cached = cache.get_cached(question, top_k)
    if cached:
        return QueryResponse(**cached, cached=True)

    # Similarity search
    results = vectorstore.similarity_search(question, top_k=top_k)
    if not results:
        return QueryResponse(
            question=question,
            answer="I could not find any relevant documents to answer your question.",
            sources=[],
            reasoning_steps=["No documents matched the query."],
        )

    # Build context string and source list
    context_parts, sources = [], []
    for doc, score in results:
        meta = doc.metadata
        context_parts.append(
            f"[Source: {meta.get('filename', 'unknown')}, chunk {meta.get('chunk_index', 0)}]\n"
            f"{doc.page_content}"
        )
        sources.append(SourceChunk(
            doc_id=meta.get("doc_id", ""),
            filename=meta.get("filename", ""),
            chunk_index=meta.get("chunk_index", 0),
            content=doc.page_content[:300],
            score=round(float(score), 4),
        ))

    context = "\n\n---\n\n".join(context_parts)

    # LLM call
    chain = _build_chain()
    raw_answer = chain.invoke({"context": context, "question": question})
    answer, steps = parse_cot_response(raw_answer)

    response = QueryResponse(
        question=question,
        answer=answer,
        sources=sources,
        reasoning_steps=steps,
    )
    cache.set_cached(question, top_k, response.model_dump())
    return response


def _extract_text(content: bytes, filename: str, mime: str) -> str:
    """Extract plain text from PDF or text files."""
    if filename.lower().endswith(".pdf") or mime == "application/pdf":
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    # Plain text fallback
    return content.decode("utf-8", errors="replace")
