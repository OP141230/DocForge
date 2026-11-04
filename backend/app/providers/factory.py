"""AI provider factory."""
from app.core.config import get_settings
from .base import AIProvider
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider
from .groq_provider import GroqProvider


def get_provider() -> AIProvider:
    """Get AI provider based on configuration."""
    settings = get_settings()
    
    if settings.AI_PROVIDER == "openai":
        return OpenAIProvider()
    elif settings.AI_PROVIDER == "groq":
        return GroqProvider()
    else:
        # Default to mock provider
        return MockProvider()
