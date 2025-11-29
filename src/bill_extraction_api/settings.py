from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Central place for environment-driven configuration."""

    model_config = SettingsConfigDict(env_prefix="BILL_API_", env_file=".env", extra="ignore")

    environment: Literal["local", "staging", "production"] = "local"
    ocr_backend: Literal["rapidocr", "dummy"] = "rapidocr"
    request_timeout_seconds: int = 120
    max_document_size_mb: int = 50
    enable_debug_artifacts: bool = False
    
    # LLM Configuration
    parser_backend: Literal["regex", "llm", "hybrid"] = "regex"
    llm_provider: Literal["openai", "anthropic", "local"] = "openai"
    llm_model: str = "gpt-4o-mini"  # Default model
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_temperature: float = 0.0  # Deterministic output
    llm_max_tokens: int = 2000


@lru_cache()
def get_settings() -> AppSettings:
    """Return cached settings instance so FastAPI can depend on it."""

    return AppSettings()
