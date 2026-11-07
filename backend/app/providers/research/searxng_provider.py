"""SearXNG search provider.

SearXNG is an open-source metasearch engine. This provider talks to an instance
the operator runs or is allowed to use, configured with ``SEARXNG_BASE_URL``. It
requires no paid key, which makes it a good self-hosted option.

The base URL is operator configuration (not user input), so loopback instances
are permitted here; user-supplied *source* URLs still go through
:mod:`app.core.url_validation`.
"""
from typing import List
from urllib.parse import urlsplit

import httpx

from app.core.config import get_settings
from .base import (
    ResearchNotConfigured,
    ResearchProvider,
    ResearchProviderError,
    ResearchTimeout,
    SearchCandidate,
)


class SearxngResearchProvider(ResearchProvider):
    """Search via a SearXNG ``/search?format=json`` endpoint."""

    name = "searxng"
    display_name = "SearXNG (self-hosted)"

    def __init__(self, base_url: str, timeout_seconds: float = 12.0):
        if not base_url:
            raise ResearchNotConfigured(
                "SEARXNG_BASE_URL is not set. Point it at your SearXNG instance "
                "or use RESEARCH_PROVIDER=none."
            )
        parts = urlsplit(base_url.strip())
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            raise ResearchNotConfigured(
                "SEARXNG_BASE_URL must be an http(s) URL, e.g. http://localhost:8080"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def health(self) -> tuple[bool, str]:
        return True, f"SearXNG instance configured at {self.base_url}"

    async def search(self, query: str, limit: int) -> List[SearchCandidate]:
        params = {
            "q": query,
            "format": "json",
            "safesearch": "1",
            "language": "en",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(f"{self.base_url}/search", params=params)
        except httpx.TimeoutException as exc:
            raise ResearchTimeout(
                f"SearXNG did not respond within {self.timeout_seconds:.0f}s"
            ) from exc
        except httpx.HTTPError as exc:
            raise ResearchProviderError(
                f"SearXNG request failed: {type(exc).__name__}"
            ) from exc

        if response.status_code == 403:
            raise ResearchProviderError(
                "SearXNG refused the request (403). Enable the JSON API on your instance."
            )
        if response.status_code >= 400:
            raise ResearchProviderError(f"SearXNG returned HTTP {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ResearchProviderError(
                "SearXNG returned a non-JSON response. Is the JSON format enabled?"
            ) from exc

        candidates: List[SearchCandidate] = []
        for item in data.get("results", []) or []:
            url = item.get("url")
            if not url:
                continue
            candidates.append(
                SearchCandidate(
                    title=str(item.get("title") or url)[:500],
                    url=url,
                    snippet=(item.get("content") or "")[:2000] or None,
                    publisher=item.get("engine") or None,
                    published_date=item.get("publishedDate"),
                    source_type_label="unknown",
                )
            )
        return candidates[:limit]


def build_provider() -> ResearchProvider:
    settings = get_settings()
    return SearxngResearchProvider(
        base_url=settings.SEARXNG_BASE_URL,
        timeout_seconds=float(settings.RESEARCH_FETCH_TIMEOUT_SECONDS),
    )
