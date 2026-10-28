import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.ollama import ollama_embed
from lightrag.llm.openai import openai_complete_if_cache

from backend.config import settings
from backend.documents import TEXT_SUFFIXES, list_document_files
from backend.rag.mineru_importer import MinerUImporter

logger = logging.getLogger(__name__)

class RAGManager:
    """Manage LightRAG lifecycle and operations."""

    def __init__(
        self,
        working_dir: str = "./storage/dicken",
        workspace: str = "ntpc_economic",
        ollama_base_url: str = "http://localhost:11434",
        neo4j_uri: str = "neo4j://127.0.0.1:7687",
        neo4j_username: str = "neo4j",
        neo4j_password: str = "",
        neo4j_database: str = "neo4j",
        openai_api_key: str = "",
        openai_model: str = "gpt-4.1-mini",
        openai_base_url: str = "https://api.openai.com/v1",
    ):
        self.working_dir = working_dir
        self.workspace = workspace
        self.ollama_base_url = ollama_base_url
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database
        self.openai_api_key = openai_api_key.strip()
        self.openai_model = openai_model
        self.openai_base_url = openai_base_url

        self.rag: Optional[LightRAG] = None
        self._initialized = False
        self.mineru_importer = MinerUImporter(settings)

    async def initialize(self) -> None:
        """Initialize LightRAG instance."""
        if self._initialized:
            logger.warning("RAG already initialized")
            return

        if not self.openai_api_key or self.openai_api_key == "your_openai_api_key_here":
            raise ValueError("Set OPENAI_API_KEY in .env before starting the RAG system.")

        logger.info(f"Initializing RAG with working_dir={self.working_dir}, model={self.openai_model}")

        # Create working directory
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        self.mineru_importer.configure()

        # Set Neo4j environment variables
        os.environ["NEO4J_URI"] = self.neo4j_uri
        os.environ["NEO4J_USERNAME"] = self.neo4j_username
        os.environ["NEO4J_PASSWORD"] = self.neo4j_password
        os.environ["NEO4J_DATABASE"] = self.neo4j_database
        
        # Translate chinese prompt
        import backend.rag.zh_prompt as zh_prompt
        zh_prompt.apply_zh_prompt()

        # Use OpenAI for generation and extraction; keep Ollama for embeddings.
        async def llm_model_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            history_messages: Optional[list] = None,
            keyword_extraction: bool = False,
            **kwargs,
        ) -> str:
            if history_messages is None:
                history_messages = []

            kwargs.pop("model_name", None)
            if keyword_extraction:
                kwargs.setdefault("response_format", {"type": "json_object"})

            return await openai_complete_if_cache(
                self.openai_model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                api_key=self.openai_api_key,
                base_url=self.openai_base_url,
                **kwargs,
            )

        # Create LightRAG instance
        self.rag = LightRAG(
            working_dir=self.working_dir,
            workspace=self.workspace,
            llm_model_func=llm_model_func,
            llm_model_name=self.openai_model,
            embedding_func=EmbeddingFunc(
                embedding_dim=1024,
                max_token_size=8192,
                func=lambda texts: ollama_embed(
                    texts,
                    embed_model="bge-m3",
                    host=self.ollama_base_url,
                ),
            ),
            llm_model_max_async=2,
            embedding_func_max_async=4,
            max_parallel_insert=2,
            graph_storage="Neo4JStorage",
            chunk_token_size=512,
            chunk_overlap_token_size=64,
        )
        # CRITICAL: Initialize storage backends
        await self.rag.initialize_storages()
        self._initialized = True
        logger.info("RAG initialization complete")

    async def finalize(self) -> None:
        """Cleanup and finalize RAG instance."""
        if self.rag:
            logger.info("Finalizing RAG...")
            await self.rag.finalize_storages()
            self._initialized = False

    async def insert_documents(
        self, texts: list[str] | str, file_paths: Optional[list[str]] = None
    ) -> None:
        """Insert documents into RAG."""
        if not self._initialized:
            raise RuntimeError("RAG not initialized. Call initialize() first.")

        if isinstance(texts, str):
            texts = [texts]

        logger.info(f"Inserting {len(texts)} documents...")
        await self.rag.ainsert(texts, file_paths=file_paths)
        logger.info("Documents inserted successfully")

    async def query(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: Optional[int] = None,
        chunk_top_k: Optional[int] = None,
        max_entity_tokens: Optional[int] = None,
        max_relation_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
    ) -> dict:
        """Query the RAG system."""
        if not self._initialized:
            raise RuntimeError("RAG not initialized. Call initialize() first.")

        top_k = settings.top_k if top_k is None else top_k
        chunk_top_k = settings.chunk_top_k if chunk_top_k is None else chunk_top_k
        max_entity_tokens = (
            settings.max_entity_tokens if max_entity_tokens is None else max_entity_tokens
        )
        max_relation_tokens = (
            settings.max_relation_tokens
            if max_relation_tokens is None
            else max_relation_tokens
        )
        max_total_tokens = (
            settings.max_total_tokens if max_total_tokens is None else max_total_tokens
        )

        logger.info(f"Querying with mode={mode}, question={question[:50]}...")

        result = await self.rag.aquery(
            question,
            param=QueryParam(
                mode=mode,
                top_k=top_k,
                chunk_top_k=chunk_top_k,
                max_entity_tokens=max_entity_tokens,
                max_relation_tokens=max_relation_tokens,
                max_total_tokens=max_total_tokens,
                stream=False,
            ),
        )

        logger.info(f"Query result: {result[:100]}...")
        return {"answer": result, "mode": mode}

    async def insert_from_files(self, directory: str) -> None:
        """Insert text/Markdown directly and binary files via built-in MinerU."""
        if not self._initialized:
            raise RuntimeError("RAG not initialized. Call initialize() first.")

        doc_dir = Path(directory)
        if not doc_dir.exists():
            logger.error(f"Directory not found: {directory}")
            return

        document_files = list_document_files(
            doc_dir, include_mineru=self.mineru_importer.config.mineru_enabled,
        )
        if not document_files:
            logger.warning(f"No supported documents found in {directory}")
            return

        logger.info(f"Found {len(document_files)} documents")

        binary_files = [p for p in document_files if p.suffix.lower() not in TEXT_SUFFIXES]
        if binary_files:
            self.mineru_importer.validate(binary_files)

        texts = []
        file_paths = []

        for document_file in document_files:
            if document_file.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                with open(document_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    texts.append(content)
                    file_paths.append(str(document_file))
                    logger.info(f"Loaded: {document_file.name}")
            except Exception as e:
                logger.error(f"Error loading {document_file}: {e}")

        if texts:
            await self.insert_documents(texts, file_paths=file_paths)
        if binary_files:
            await self.mineru_importer.insert(self.rag, binary_files)

    def get_status(self) -> dict:
        """Get RAG status."""
        return {
            "initialized": self._initialized,
            "working_dir": self.working_dir,
            "workspace": self.workspace,
        }
