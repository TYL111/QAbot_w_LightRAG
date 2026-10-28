import logging
import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from backend.rag.rag_manager import RAGManager
from backend.scraper.crawler import Crawler
from backend.config import settings
from backend.documents import TEXT_SUFFIXES, list_document_files
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
_scrape_status = {
    "running": False,
    "progress": 0,
    "processed": 0,
    "saved": 0,
    "pending": 0,
    "max_pages": None,
    "error": None,
    "paused": False,
}
_active_crawler: Crawler | None = None
_scrape_pause_event: asyncio.Event | None = None
_refresh_status = {"running": False, "error": None}

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
            Path("./data"),
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

        for idx, doc_file in enumerate(list_document_files(
            docs_path, include_mineru=settings.mineru_enabled,
        )):
            try:
                if doc_file.suffix.lower() not in TEXT_SUFFIXES:
                    # Binary source size is not the parsed text length. Do not
                    # decode PDF/Office/images as UTF-8 or invent chunk counts.
                    documents.append(Document(
                        id=f"doc_{idx}", title=doc_file.name, url="",
                        content_length=0, chunks=0,
                        timestamp=str(doc_file.stat().st_mtime),
                    ))
                    continue
                with open(doc_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                    # Extract title and URL with better parsing
                    title = next((line.strip()[:50] for line in lines if line.strip()), f"Document {idx}")
                    url = ""

                    for line in lines[:5]:  # Check first 5 lines
                        if line.startswith("Title:"):
                            title = line.replace("Title:", "").strip()
                            break
                        elif line.startswith("# "):
                            title = line[2:].strip()
                            break

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
        max_pages = (
            request.max_pages
            if request.max_pages is not None
            else settings.scrape_max_pages
        )
        max_depth = request.max_depth if request.max_depth is not None else settings.scrape_max_depth
        delay_seconds = (
            request.delay_seconds
            if request.delay_seconds is not None
            else settings.scrape_delay_seconds
        )
        logger.info(
            "Scrape requested: max_pages=%s, max_depth=%s, delay_seconds=%s",
            max_pages,
            max_depth,
            delay_seconds,
        )
        _scrape_status.update(
            running=True,
            progress=0,
            processed=0,
            saved=0,
            pending=1,
            max_pages=max_pages,
            error=None,
            paused=False,
        )

        async def run_scrape():
            global _active_crawler, _scrape_pause_event
            _scrape_status["running"] = True
            _scrape_status["progress"] = 0
            _scrape_status["processed"] = 0
            _scrape_status["saved"] = 0
            _scrape_status["pending"] = 1
            _scrape_status["max_pages"] = max_pages
            _scrape_status["error"] = None
            _scrape_pause_event = asyncio.Event()
            _scrape_pause_event.set()

            def update_progress(processed: int, saved: int, pending: int) -> None:
                _scrape_status["processed"] = processed
                _scrape_status["saved"] = saved
                _scrape_status["pending"] = pending
                _scrape_status["progress"] = round(processed / max_pages * 100, 1)

            try:
                crawler = Crawler(
                    root_url=settings.scrape_base_url,
                    output_dir="./data",
                    max_depth=max_depth,
                    max_pages=max_pages,
                    delay_seconds=delay_seconds,
                    progress_callback=update_progress,
                    pause_event=_scrape_pause_event,
                )
                _active_crawler = crawler

                saved_files = await crawler.crawl_and_save()
                _scrape_status["progress"] = 100
                logger.info("Crawling completed: %s files saved to ./data", len(saved_files))

            except Exception as e:
                logger.error(f"Scraping error: {e}")
                _scrape_status["error"] = str(e)
                _scrape_status["running"] = False
                raise
            finally:
                _scrape_status["running"] = False
                _scrape_status["paused"] = False
                _active_crawler = None
                _scrape_pause_event = None

        background_tasks.add_task(run_scrape)

        return {
            "status": "started",
            "message": f"Scraping {settings.scrape_base_url}...",
        }
    except Exception as e:
        logger.error(f"Scrape endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scrape/pause")
async def pause_scrape() -> dict:
    if not _scrape_status["running"] or _scrape_pause_event is None:
        raise HTTPException(status_code=409, detail="No active scrape to pause")
    _scrape_pause_event.clear()
    _scrape_status["paused"] = True
    logger.info("Scraping paused")
    return {"status": "paused"}

@router.post("/scrape/resume")
async def resume_scrape() -> dict:
    if not _scrape_status["running"] or _scrape_pause_event is None:
        raise HTTPException(status_code=409, detail="No active scrape to resume")
    _scrape_pause_event.set()
    _scrape_status["paused"] = False
    logger.info("Scraping resumed")
    return {"status": "resumed"}

@router.get("/scrape/status")
async def get_scrape_status() -> dict:
    """Return the current scraper progress."""
    return dict(_scrape_status)

@router.post("/refresh")
async def refresh(
    request: RefreshRequest,
    background_tasks: BackgroundTasks,
    rag: RAGManager = Depends(get_rag),
) -> dict:
    """Rebuild RAG from latest raw data."""
    try:
        if _refresh_status["running"]:
            raise HTTPException(status_code=409, detail="Refresh already in progress")

        _refresh_status.update(running=True, error=None)

        async def run_refresh():
            try:
                output_dir = request.output_dir or "./data"
                docs_dir = Path(output_dir)
                if not docs_dir.exists():
                    raise FileNotFoundError(f"Crawler output directory not found: {docs_dir}")

                await rag.insert_from_files(str(docs_dir))

                logger.info("Refresh completed")
            except Exception as e:
                logger.error(f"Refresh error: {e}")
                _refresh_status["error"] = str(e)
                raise
            finally:
                _refresh_status["running"] = False

        background_tasks.add_task(run_refresh)

        return {
            "status": "started",
            "message": "Rebuilding RAG from latest data...",
        }
    except Exception as e:
        logger.error(f"Refresh endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/refresh/status")
async def get_refresh_status() -> dict:
    """Return the current refresh status."""
    return dict(_refresh_status)

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
        "scrape_max_depth": settings.scrape_max_depth,
        "working_dir": settings.working_dir,
        "top_k": settings.top_k,
        "chunk_top_k": settings.chunk_top_k,
        "max_total_tokens": settings.max_total_tokens,
    }

@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now()}
