import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import SecretStr
from typing import Literal

class Settings(BaseSettings):
    # OpenAI LLM
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Neo4j
    neo4j_uri: str = "neo4j://127.0.0.1:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"

    # FastAPI
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # LightRAG
    working_dir: str = "./storage/dicken"
    workspace: str = "ntpc_economic"

    # LightRAG's built-in MinerU HTTP parser (no models in the API process).
    mineru_enabled: bool = True
    mineru_api_mode: Literal["local", "official"] = "local"
    mineru_local_endpoint: str = "http://127.0.0.1:8100"
    mineru_api_token: SecretStr = SecretStr("")
    mineru_official_endpoint: str = "https://mineru.net"
    mineru_input_dir: str = "./storage/mineru_inputs"
    mineru_additional_suffixes: str = ""
    mineru_language: str = "ch"
    mineru_local_backend: str = "pipeline"
    mineru_local_parse_method: Literal["auto", "txt", "ocr"] = "auto"
    mineru_enable_table: bool = True
    mineru_enable_formula: bool = True

    # Query Parameters
    top_k: int = 60
    chunk_top_k: int = 20
    max_entity_tokens: int = 6000
    max_relation_tokens: int = 8000
    max_total_tokens: int = 30000

    # Web Scraper
    scrape_base_url: str = 'https://www.economic.ntpc.gov.tw'
    scrape_max_pages: int = 100
    scrape_max_depth: int = 2
    scrape_delay_seconds: float = 2.0

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    """Get settings from environment variables."""
    return Settings()

settings = get_settings()
