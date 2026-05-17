import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.rag.rag_manager import RAGManager
from backend.scraper.ntpc_scraper import NTPCEconomicScraper
from backend.scraper.data_processor import DataProcessor
from backend.config import settings
from backend.dependencies import get_rag
from backend.api.schemas import (
    QueryRequest,
    QueryResponse,
    Source,
    DocumentsResponse,
    Document,
    StatusResponse,
    ErrorResponse,
    ScrapeRequest,
    RefreshRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["rag"])

# Global state for background tasks
_scrape_status = {"running": False, "progress": 0}

@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    rag: RAGManager = Depends(get_rag),
) -> QueryResponse:
    """Submit a question to the RAG system."""
    try:
        result = await rag.query(
            question=request.question,
            mode=request.mode,
            top_k=request.top_k,
            chunk_top_k=request.chunk_top_k,
        )

        # Parse response to extract sources (simplified)
        # In production, would parse more complex response format
        answer = result.get("answer", "")

        return QueryResponse(
            answer=answer,
            sources=[],  # Would extract from LightRAG response
            mode=request.mode,
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=DocumentsResponse)
async def get_documents(
    rag: RAGManager = Depends(get_rag),
) -> DocumentsResponse:
    """Get list of indexed documents."""
    try:
        documents = []

        # Check multiple possible document locations
        possible_paths = [
            Path(settings.working_dir) / "data" / "docs",
            Path(settings.working_dir) / "docs",
        ]

        docs_path = None
        for path in possible_paths:
            if path.exists():
                docs_path = path
                logger.info(f"Found documents at: {path}")
                break

        if not docs_path:
            logger.info(f"No document directories found. Checked: {possible_paths}")
            return DocumentsResponse(total=0, documents=[])

        for idx, doc_file in enumerate(sorted(docs_path.glob("*.txt"))):
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                    # Extract title and URL with better parsing
                    title = f"Document {idx}"
                    url = ""

                    for line in lines[:5]:  # Check first 5 lines
                        if line.startswith("Title:"):
                            title = line.replace("Title:", "").strip()
                            break
                        elif line.strip() and not url:  # Use first non-empty line as fallback
                            title = line.strip()[:50]

                    for line in lines[:5]:
                        if line.startswith("URL:"):
                            url = line.replace("URL:", "").strip()
                            break

                    documents.append(
                        Document(
                            id=f"doc_{idx}",
                            title=title or f"Document {idx}",
                            url=url,
                            content_length=len(content),
                            chunks=max(1, len(content) // 300),
                            timestamp=str(doc_file.stat().st_mtime),
                        )
                    )
                    logger.debug(f"Parsed doc {idx}: title='{title}' url='{url}'")
            except Exception as e:
                logger.warning(f"Error reading {doc_file}: {e}")
                # Still add document even if parsing fails
                documents.append(
                    Document(
                        id=f"doc_{idx}",
                        title=f"Document {idx} (parse error)",
                        url="",
                        content_length=0,
                        chunks=0,
                        timestamp="0",
                    )
                )
                continue

        logger.info(f"Returning {len(documents)} documents")
        return DocumentsResponse(total=len(documents), documents=documents)
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape")
async def scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Trigger web scraping of NTPC economic website."""
    if _scrape_status["running"]:
        raise HTTPException(status_code=409, detail="Scraping already in progress")

    try:
        async def run_scrape():
            _scrape_status["running"] = True
            _scrape_status["progress"] = 0

            try:
                scraper = NTPCEconomicScraper(
                    base_url=settings.scrape_base_url,
                    max_pages=request.max_pages,
                    delay_seconds=request.delay_seconds,
                )

                # Create output directory
                output_dir = Path(settings.working_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_file = output_dir / "ntpc_raw.json"

                await scraper.scrape_and_save(str(output_file))
                _scrape_status["progress"] = 100
                logger.info(f"Scraping completed: {output_file}")

            except Exception as e:
                logger.error(f"Scraping error: {e}")
                _scrape_status["running"] = False
                raise
            finally:
                _scrape_status["running"] = False

        background_tasks.add_task(run_scrape)

        return {
            "status": "started",
            "message": f"Scraping {settings.scrape_base_url}...",
        }
    except Exception as e:
        logger.error(f"Scrape endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh(
    request: RefreshRequest,
    background_tasks: BackgroundTasks,
    rag: RAGManager = Depends(get_rag),
) -> dict:
    """Rebuild RAG from latest raw data."""
    try:
        async def run_refresh():
            try:
                raw_file = request.raw_data_file or Path(settings.working_dir) / "ntpc_raw.json"
                output_dir = request.output_dir or str(Path(settings.working_dir) / "data")

                # Process raw data
                logger.info(f"Processing raw data from {raw_file}")
                cleaned_data = DataProcessor.load_and_process(str(raw_file), output_dir)

                # Insert into RAG
                docs_dir = Path(output_dir) / "docs"
                if docs_dir.exists():
                    await rag.insert_from_files(str(docs_dir))

                logger.info("Refresh completed")
            except Exception as e:
                logger.error(f"Refresh error: {e}")
                raise

        background_tasks.add_task(run_refresh)

        return {
            "status": "started",
            "message": "Rebuilding RAG from latest data...",
        }
    except Exception as e:
        logger.error(f"Refresh endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status(
    rag: RAGManager = Depends(get_rag),
) -> StatusResponse:
    """Get server and RAG status."""
    try:
        status = rag.get_status()
        return StatusResponse(
            initialized=status["initialized"],
            working_dir=status["working_dir"],
            workspace=status["workspace"],
            timestamp=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_config() -> dict:
    """Get current configuration."""
    return {
        "scrape_base_url": settings.scrape_base_url,
        "scrape_max_pages": settings.scrape_max_pages,
        "working_dir": settings.working_dir,
        "top_k": settings.top_k,
        "chunk_top_k": settings.chunk_top_k,
        "max_total_tokens": settings.max_total_tokens,
    }

@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now()}
