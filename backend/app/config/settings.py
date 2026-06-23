"""Application configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import List

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

    # AI / Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"

    # ChromaDB
    chroma_db_path: str = str(PROJECT_ROOT / "backend" / "data" / "chromadb")

    # Storage
    upload_directory: str = "./data/uploads"

    # OCR
    ocr_language: str = "en"

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
