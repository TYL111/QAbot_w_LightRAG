import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.ollama import ollama_embed, ollama_model_complete

from backend.config import settings

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
    ):
        self.working_dir = working_dir
        self.workspace = workspace
        self.ollama_base_url = ollama_base_url
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database

        self.rag: Optional[LightRAG] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize LightRAG instance."""
        if self._initialized:
            logger.warning("RAG already initialized")
            return

        logger.info(f"Initializing RAG with working_dir={self.working_dir}")

        # Create working directory
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)

        # Set Neo4j environment variables
        os.environ["NEO4J_URI"] = self.neo4j_uri
        os.environ["NEO4J_USERNAME"] = self.neo4j_username
        os.environ["NEO4J_PASSWORD"] = self.neo4j_password
        os.environ["NEO4J_DATABASE"] = self.neo4j_database
        
        # Translate chinese prompt
        import backend.rag.zh_prompt as zh_prompt
        zh_prompt.apply_zh_prompt()

        # Define LLM function using Ollama
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
            kwargs.setdefault("options", {"num_ctx": 12288})

            return await ollama_model_complete(
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                host=self.ollama_base_url,
                **kwargs,
            )

        # Create LightRAG instance
        self.rag = LightRAG(
            working_dir=self.working_dir,
            workspace=self.workspace,
            llm_model_func=llm_model_func,
            llm_model_name="qwen2.5:14b",
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
        """Insert documents from a directory of text files."""
        if not self._initialized:
            raise RuntimeError("RAG not initialized. Call initialize() first.")

        doc_dir = Path(directory)
        if not doc_dir.exists():
            logger.error(f"Directory not found: {directory}")
            return

        txt_files = list(doc_dir.glob("*.txt"))
        if not txt_files:
            logger.warning(f"No .txt files found in {directory}")
            return

        logger.info(f"Found {len(txt_files)} text files")

        texts = []
        file_paths = []

        for txt_file in sorted(txt_files):
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    texts.append(content)
                    file_paths.append(str(txt_file))
                    logger.info(f"Loaded: {txt_file.name}")
            except Exception as e:
                logger.error(f"Error loading {txt_file}: {e}")

        if texts:
            await self.insert_documents(texts, file_paths=file_paths)

    def get_status(self) -> dict:
        """Get RAG status."""
        return {
            "initialized": self._initialized,
            "working_dir": self.working_dir,
            "workspace": self.workspace,
        }
