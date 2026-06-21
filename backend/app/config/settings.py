"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import List


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
    chroma_db_path: str = "./data/chromadb"

    # Storage
    upload_directory: str = "./data/uploads"

    # OCR
    ocr_language: str = "en"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
