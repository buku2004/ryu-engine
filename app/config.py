"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration — all values come from .env or environment."""

    # App
    app_name: str = "Ryu Engine"
    debug: bool = False

    # Typesense
    typesense_host: str = "localhost"
    typesense_port: int = 8108
    typesense_protocol: str = "http"
    typesense_api_key: str = "xyz"
    typesense_collection: str = "posts"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "posts"

    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768

    # LLM
    llm_provider: str = "gemini"  # "openai" or "gemini"
    openai_chat_model: str = "gpt-4"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Reddit
    reddit_user_agent: str = "ryu-engine/1.0"

    # Search
    hybrid_k: int = 60  # RRF constant
    default_search_limit: int = 10

    # PDF summarization guardrails (free-tier friendly)
    pdf_summary_max_input_chars: int = 8000
    pdf_summary_fetch_timeout_sec: int = 25
    pdf_summary_max_calls_per_hour: int = 20
    pdf_summary_cache_ttl_sec: int = 86400

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
