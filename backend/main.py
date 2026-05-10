import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import settings
from backend.api import routes
from backend.rag.rag_manager import RAGManager

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("Starting NTPC Economic QA Bot API...")

    # Initialize RAG on startup
    try:
        logger.info("Initializing RAG system...")
        rag_manager = RAGManager(
            working_dir=settings.working_dir,
            workspace=settings.workspace,
            gemini_api_key=settings.gemini_api_key,
            ollama_base_url=settings.ollama_base_url,
            neo4j_uri=settings.neo4j_uri,
            neo4j_username=settings.neo4j_username,
            neo4j_password=settings.neo4j_password,
            neo4j_database=settings.neo4j_database,
        )
        await rag_manager.initialize()
        logger.info("✅ RAG system initialized successfully")
        app.state.rag = rag_manager
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG: {e}")
        raise

    yield

    logger.info("Shutting down...")
    if hasattr(app.state, 'rag'):
        try:
            await app.state.rag.finalize()
            logger.info("RAG finalized")
        except Exception as e:
            logger.error(f"Error finalizing RAG: {e}")

# Create FastAPI app
app = FastAPI(
    title="NTPC Economic Development QA Bot",
    description="RAG-based QA system for NTPC economic information",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router)

# Serve static frontend files
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

@app.get("/")
async def root():
    """Serve frontend or API docs."""
    if frontend_dist.exists():
        return FileResponse(frontend_dist / "index.html")
    return {"message": "NTPC Economic QA Bot API. Docs at /docs"}

@app.get("/api/")
async def api_root():
    """API root endpoint."""
    return {
        "name": "NTPC Economic Development QA Bot",
        "version": "2.0.0",
        "status": "running",
    }

if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path

    # Add parent directory to path so backend module can be imported
    sys.path.insert(0, str(Path(__file__).parent.parent))

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
