import logging
from typing import AsyncGenerator
from fastapi import Request
from backend.rag.rag_manager import RAGManager

logger = logging.getLogger(__name__)

async def get_rag(request: Request) -> AsyncGenerator[RAGManager, None]:
    """Dependency injection for RAG manager from app state."""
    if not hasattr(request.app.state, 'rag'):
        raise RuntimeError("RAG not initialized. Check server startup logs.")

    rag = request.app.state.rag
    if not rag._initialized:
        raise RuntimeError("RAG not properly initialized.")

    yield rag
