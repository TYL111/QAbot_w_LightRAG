from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Request Models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    question: str
    mode: str = "hybrid"  # local, global, hybrid, mix, naive
    top_k: int = 60
    chunk_top_k: int = 20

class ScrapeRequest(BaseModel):
    """Request model for scrape endpoint."""
    max_pages: Optional[int] = Field(default=None, gt=0)
    max_depth: Optional[int] = Field(default=None, ge=0)
    delay_seconds: Optional[float] = Field(default=None, ge=0)

class RefreshRequest(BaseModel):
    """Request model for refresh endpoint."""
    output_dir: Optional[str] = None

# Response Models
class Source(BaseModel):
    """Source citation for answer."""
    title: str
    url: str
    excerpt: str

class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sources: list[Source] = []
    mode: str
    timestamp: datetime

class Document(BaseModel):
    """Document metadata."""
    id: str
    title: str
    url: str
    content_length: int
    chunks: int
    timestamp: str

class DocumentsResponse(BaseModel):
    """Response model for documents list."""
    total: int
    documents: list[Document] = []

class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    initialized: bool
    working_dir: str
    workspace: str
    timestamp: datetime

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
