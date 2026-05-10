from pydantic import BaseModel
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
    max_pages: int = 100
    delay_seconds: float = 2.0

class RefreshRequest(BaseModel):
    """Request model for refresh endpoint."""
    raw_data_file: Optional[str] = None
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
