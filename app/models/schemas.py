from pydantic import BaseModel, Field
from typing import Optional


class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_indexed: int
    message: str


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    chunks: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class SourceChunk(BaseModel):
    doc_id: str
    filename: str
    chunk_index: int
    content: str
    score: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]
    cached: bool = False
    reasoning_steps: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    ollama: str
    chromadb: str
    redis: str
    version: str = "0.1.0"
