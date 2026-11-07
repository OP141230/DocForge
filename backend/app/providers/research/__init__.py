"""Research provider implementations (Phase 5)."""
from .base import (
    ProviderStatus,
    ResearchNotConfigured,
    ResearchProvider,
    ResearchProviderError,
    ResearchTimeout,
    SearchCandidate,
)
from .factory import SUPPORTED_PROVIDERS, get_provider_status, get_research_provider
from .none_provider import UnavailableResearchProvider

__all__ = [
    "SearchCandidate",
    "ResearchProvider",
    "ResearchProviderError",
    "ResearchNotConfigured",
    "ResearchTimeout",
    "ProviderStatus",
    "UnavailableResearchProvider",
    "get_research_provider",
    "get_provider_status",
    "SUPPORTED_PROVIDERS",
]
