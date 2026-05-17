import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Gemini API
    gemini_api_key: str

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

    # Query Parameters
    top_k: int = 60
    chunk_top_k: int = 20
    max_entity_tokens: int = 6000
    max_relation_tokens: int = 8000
    max_total_tokens: int = 30000

    # Web Scraper
    scrape_base_url: str = 'https://www.economic.ntpc.gov.tw'
    scrape_max_pages: int = 100
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
