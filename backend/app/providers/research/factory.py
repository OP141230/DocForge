"""Research provider factory.

Resolution order is configuration -> provider instance -> honest fallback.
A misconfiguration (missing key, unknown name) produces an
:class:`UnavailableResearchProvider` carrying a human-readable reason rather than
an exception at import time, so the rest of the app keeps working and the UI can
say *why* research is off.
"""
from typing import Optional

from app.core.config import Settings, get_settings
from .base import ProviderStatus, ResearchNotConfigured, ResearchProvider
from .none_provider import DEFAULT_REASON, UnavailableResearchProvider

SUPPORTED_PROVIDERS = ("none", "tavily", "searxng")


def get_research_provider(
    settings: Optional[Settings] = None,
    name_override: Optional[str] = None,
) -> ResearchProvider:
    """Build the configured research provider.

    ``name_override`` is used by tests to select a provider without touching
    global settings.
    """
    settings = settings or get_settings()
    name = (name_override or settings.RESEARCH_PROVIDER or "none").strip().lower()

    if name in ("", "none", "off", "disabled"):
        return UnavailableResearchProvider()

    try:
        if name == "tavily":
            from .tavily_provider import TavilyResearchProvider

            return TavilyResearchProvider(
                api_key=settings.TAVILY_API_KEY,
                timeout_seconds=float(settings.RESEARCH_FETCH_TIMEOUT_SECONDS),
            )
        if name == "searxng":
            from .searxng_provider import SearxngResearchProvider

            return SearxngResearchProvider(
                base_url=settings.SEARXNG_BASE_URL,
                timeout_seconds=float(settings.RESEARCH_FETCH_TIMEOUT_SECONDS),
            )
    except ResearchNotConfigured as exc:
        return UnavailableResearchProvider(str(exc))

    return UnavailableResearchProvider(
        f"Unknown RESEARCH_PROVIDER '{name}'. Supported values: "
        f"{', '.join(SUPPORTED_PROVIDERS)}. {DEFAULT_REASON}"
    )


async def get_provider_status(
    settings: Optional[Settings] = None,
) -> ProviderStatus:
    """Status payload used by ``GET /api/research/providers``."""
    provider = get_research_provider(settings)
    available, message = await provider.health()
    return ProviderStatus(
        name=provider.name,
        display_name=provider.display_name,
        available=available,
        message=message,
        is_external=provider.is_external,
        notes=[
            "External results are references, not verified facts.",
            "Tools: knowledge-base sources and any URLs you add always work.",
        ],
    )
