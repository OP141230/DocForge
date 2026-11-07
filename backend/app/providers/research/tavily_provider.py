"""Tavily search provider.

Tavily is used as the default *external* option because it is a search API
designed for LLM grounding, has a free tier, returns titles/URLs/snippets
directly, and needs a single key. It is still optional: DocForge's research
pipeline works over uploaded knowledge-base files and user-supplied URLs with no
key at all.

Terms of service: results are used as references, we do not republish page
bodies, and every fetched page is treated as untrusted data.
"""
from typing import List

import httpx

from app.core.config import get_settings
from .base import (
    ResearchNotConfigured,
    ResearchProvider,
    ResearchProviderError,
    ResearchTimeout,
    SearchCandidate,
)

TAVILY_ENDPOINT = "https://api.tavily.com/search"


class TavilyResearchProvider(ResearchProvider):
    """Search via the Tavily API."""

    name = "tavily"
    display_name = "Tavily Search API"

    def __init__(self, api_key: str, timeout_seconds: float = 12.0):
        if not api_key:
            raise ResearchNotConfigured(
                "TAVILY_API_KEY is not set. Add it to .env or use RESEARCH_PROVIDER=none."
            )
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def health(self) -> tuple[bool, str]:
        return True, "Tavily API key configured"

    async def search(self, query: str, limit: int) -> List[SearchCandidate]:
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max(1, min(limit, 10)),
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(TAVILY_ENDPOINT, json=payload)
        except httpx.TimeoutException as exc:
            raise ResearchTimeout(
                f"Tavily did not respond within {self.timeout_seconds:.0f}s"
            ) from exc
        except httpx.HTTPError as exc:
            # Never echo the request payload (it contains the key).
            raise ResearchProviderError(
                f"Tavily request failed: {type(exc).__name__}"
            ) from exc

        if response.status_code == 401:
            raise ResearchProviderError("Tavily rejected the API key (401)")
        if response.status_code == 429:
            raise ResearchProviderError("Tavily rate limit reached (429)")
        if response.status_code >= 400:
            raise ResearchProviderError(
                f"Tavily returned HTTP {response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ResearchProviderError("Tavily returned a malformed response") from exc

        candidates: List[SearchCandidate] = []
        for item in data.get("results", []) or []:
            url = item.get("url")
            title = item.get("title") or url
            if not url:
                continue
            candidates.append(
                SearchCandidate(
                    title=str(title)[:500],
                    url=url,
                    snippet=(item.get("content") or "")[:2000] or None,
                    published_date=item.get("published_date"),
                    source_type_label=_label_from_url(url),
                )
            )
        return candidates[:limit]


def _label_from_url(url: str) -> str:
    """Cheap heuristic label; refined during source evaluation."""
    lowered = url.lower()
    if any(domain in lowered for domain in ("arxiv.org", "doi.org", "pubmed", "nature.com", "science.org", "springer", "ieee.org", "acm.org", "sciencedirect")):
        return "peer_reviewed"
    if ".gov" in lowered or ".gov." in lowered:
        return "government"
    if ".edu" in lowered:
        return "academic"
    if any(domain in lowered for domain in ("docs.", "developer.", "readthedocs", "wikipedia.org")):
        return "reference"
    if any(domain in lowered for domain in ("news", "reuters", "bbc.", "nytimes", "theguardian", "apnews")):
        return "news"
    return "unknown"


def build_provider() -> ResearchProvider:
    """Construct from settings (raises ResearchNotConfigured when unusable)."""
    settings = get_settings()
    return TavilyResearchProvider(
        api_key=settings.TAVILY_API_KEY,
        timeout_seconds=float(settings.RESEARCH_FETCH_TIMEOUT_SECONDS),
    )
