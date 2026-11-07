"""The explicit "no external research" provider.

This exists so the pipeline has something honest to talk to when no search
provider is configured. It never returns results: external research is simply
reported as unavailable, and the UI shows that instead of pretending a search
happened. Knowledge-base sources and user-provided URLs still work.

Returning invented or cached "example" results here would violate the Phase 5
rule that a source must never be fabricated, so this class only raises.
"""
from typing import List

from .base import (
    ResearchNotConfigured,
    ResearchProvider,
    SearchCandidate,
)

DEFAULT_REASON = (
    "No external research provider is configured. Set RESEARCH_PROVIDER=tavily "
    "with TAVILY_API_KEY, or RESEARCH_PROVIDER=searxng with SEARXNG_BASE_URL. "
    "Uploaded knowledge-base files and URLs you add yourself are still used."
)


class UnavailableResearchProvider(ResearchProvider):
    """A provider that reports why external search is unavailable."""

    name = "none"
    display_name = "External search disabled"
    is_external = False

    def __init__(self, reason: str = DEFAULT_REASON):
        self.reason = reason

    async def search(self, query: str, limit: int) -> List[SearchCandidate]:
        raise ResearchNotConfigured(self.reason)

    async def health(self) -> tuple[bool, str]:
        return False, self.reason
