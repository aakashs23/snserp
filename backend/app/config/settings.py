"""Application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root (SNSERP/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Sri Naga Sai ERP"
    app_env: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/snserp"

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # Authentication
    jwt_secret: str = "dev-secret-change-in-production"
    enable_registration: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Upload limits
    max_upload_size_mb: int = 20

    # Rate limits (requests per minute)
    rate_limit_auth: str = "10/minute"
    rate_limit_ai: str = "20/minute"
    rate_limit_upload: str = "10/minute"
    rate_limit_default: str = "100/minute"

    # AI / Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"

    # AI Provider Configuration
    ai_primary_provider: str = "gemini"       # ollama | gemini | grok
    ai_fallback_provider: str = "grok"      # ollama | gemini | grok | none
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    xai_api_key: str = ""
    grok_model: str = "grok-3-mini"

    # AI Resilience — tune per provider latency and rate limits
    ai_request_timeout_seconds: float = 30.0
    ai_max_concurrent_requests: int = 8
    ai_circuit_breaker_threshold: int = 3
    ai_circuit_breaker_reset_seconds: float = 30.0

    # ChromaDB
    chroma_db_path: str = str(PROJECT_ROOT / "backend" / "data" / "chromadb")

    # Storage
    upload_directory: str = "./data/uploads"

    # OCR
    ocr_language: str = "en"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept a few environment-style debug flags without crashing reloads."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()

os.makedirs(settings.chroma_db_path, exist_ok=True)
