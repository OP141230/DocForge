"""Application configuration management."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


# Determine .env file path at module load time
_env_file = Path(__file__).parent.parent.parent / ".env"
if not _env_file.exists():
    _env_file = Path(".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # AI Provider
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_MAX_RETRIES: int = 3
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_MAX_RETRIES: int = 3
    
    # Database
    DATABASE_URL: str = "sqlite:///./docforge.db"
    
    # API Configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Application
    APP_NAME: str = "DocForge"
    APP_VERSION: str = "1.0.0"
    
    # Phase 4: Knowledge Base Configuration
    UPLOAD_MAX_SIZE_MB: int = 50
    UPLOAD_STORAGE_PATH: str = "./uploads"
    UPLOAD_ALLOWED_EXTENSIONS: str = "pdf,docx,txt,md,html,csv"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Phase 5: Research configuration
    # 'none' = no external web search (knowledge base + user URLs still work)
    RESEARCH_PROVIDER: str = "none"
    TAVILY_API_KEY: str = ""
    SEARXNG_BASE_URL: str = ""
    RESEARCH_MAX_QUESTIONS: int = 6
    RESEARCH_RESULTS_PER_QUESTION: int = 5
    RESEARCH_MAX_SOURCES: int = 20
    RESEARCH_MAX_USER_URLS: int = 10
    RESEARCH_FETCH_TIMEOUT_SECONDS: int = 12
    RESEARCH_MAX_PAGE_BYTES: int = 2_000_000
    RESEARCH_MAX_REDIRECTS: int = 3
    RESEARCH_MIN_PASSAGE_CHARS: int = 120
    RESEARCH_REQUEST_LIMIT_PER_MINUTE: int = 10

    # Phase 5: Citations & verification
    CITATION_DEFAULT_STYLE: str = "apa"
    VERIFICATION_MAX_CLAIMS: int = 40
    VERIFICATION_MIN_LEXICAL_OVERLAP: float = 0.18
    VERIFICATION_REQUEST_LIMIT_PER_MINUTE: int = 10
    
    model_config = SettingsConfigDict(
        env_file=str(_env_file),
        case_sensitive=True,
        env_file_encoding='utf-8',
        extra='ignore'  # Ignore extra fields in .env
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def reload_settings() -> Settings:
    """Clear cache and reload settings."""
    get_settings.cache_clear()
    return get_settings()
