from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import DocumentUploadResponse, DocumentListResponse, DocumentInfo
from app.services import rag, vectorstore

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"application/pdf", "text/plain"}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a document (PDF or plain text)."""
    ext = "." + (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit.",
        )
    logger.info("document_upload_received", filename=file.filename, size_mb=round(size_mb, 2))
    try:
        result = rag.ingest_document(content, file.filename or "upload", file.content_type or "text/plain")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return result


@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    """List all indexed documents."""
    docs = vectorstore.list_documents()
    return DocumentListResponse(
        documents=[DocumentInfo(**d) for d in docs],
        total=len(docs),
    )


@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
async def delete_document(doc_id: str):
    """Remove all chunks of a document from the vector store."""
    removed = vectorstore.delete_document(doc_id)
    if removed == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return {"doc_id": doc_id, "chunks_removed": removed}
