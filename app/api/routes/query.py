from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import QueryRequest, QueryResponse
from app.services import rag

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Ask a question against all indexed documents using Chain-of-Thought RAG."""
    top_k = request.top_k or settings.top_k
    logger.info("query_received", question=request.question[:80], top_k=top_k)
    try:
        return rag.answer_question(request.question, top_k=top_k)
    except Exception as exc:
        logger.error("query_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your query.",
        )
