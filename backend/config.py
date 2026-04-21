"""Application configuration."""

from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Book Learning Studio"
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Paths
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    CACHE_DIR: Path = BASE_DIR / "data" / "cache"

    # Database
    SQLITE_URL: str = f"sqlite:///{BASE_DIR}/data/db.sqlite"

    # Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: str

    # Embeddings
    EMBEDDING_MODEL: str = "google/embeddinggemma-300m"

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # LLM
    LLM_PROVIDER: str = "anthropic"
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # RAG
    RAG_TOP_K: int = 6

    # Upload
    MAX_UPLOAD_MB: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() # type: ignore

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)