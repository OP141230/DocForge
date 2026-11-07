"""Research (web search) provider abstraction.

Why an abstraction instead of calling one API directly?
------------------------------------------------------
Search providers differ in price, rate limits, result quality and terms of
service. Keeping the pipeline behind :class:`ResearchProvider` means the
research service never imports a vendor SDK, so swapping Tavily for SearXNG (or
adding Brave later) is a factory change, not a rewrite of the pipeline -
the same pattern Phase 1 already uses for ``AIProvider``.

Contract
--------
A provider returns *candidates*: title, URL and a short snippet. It does **not**
return page text - fetching and extracting content is the pipeline's job, which
keeps SSRF protection in one place (:mod:`app.services.source_fetcher`).

Providers must raise :class:`ResearchProviderError` subclasses rather than
returning invented data when something fails. The pipeline records the failure
and reports it; it never fabricates results to look functional.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class SearchCandidate:
    """One search result, before the page is fetched."""

    title: str
    url: str
    snippet: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    source_type_label: str = "unknown"


class ResearchProviderError(Exception):
    """Base class for provider failures.

    Messages must never contain API keys or full request bodies.
    """


class ResearchNotConfigured(ResearchProviderError):
    """No usable provider is configured (or its credentials are missing)."""


class ResearchTimeout(ResearchProviderError):
    """The provider did not answer within the configured timeout."""


class ResearchProvider(ABC):
    """Interface every search provider implements."""

    name: str = "base"
    display_name: str = "Base"
    is_external: bool = True

    @abstractmethod
    async def search(self, query: str, limit: int) -> List[SearchCandidate]:
        """Search for ``query`` and return at most ``limit`` candidates."""

    async def health(self) -> tuple[bool, str]:
        """Return ``(usable, human readable reason)`` without network calls."""
        return True, "configured"


@dataclass
class ProviderStatus:
    """Serializable provider status for the API and the UI."""

    name: str
    display_name: str
    available: bool
    message: str
    is_external: bool = True
    notes: List[str] = field(default_factory=list)
