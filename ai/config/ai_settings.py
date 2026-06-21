"""AI service configuration."""

from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    """Settings for AI services."""

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:8b"
    embedding_model: str = "nomic-embed-text"

    # ChromaDB
    chroma_db_path: str = "./data/chromadb"
    chroma_collection_name: str = "snserp_documents"

    # OCR
    ocr_language: str = "en"

    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_document_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


ai_settings = AISettings()
