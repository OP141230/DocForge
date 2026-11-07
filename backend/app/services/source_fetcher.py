"""SSRF-safe HTTP fetching for research sources.

Everything about this module is deliberately conservative:

* redirects are followed **manually** so each hop is re-validated (an attacker
  cannot redirect a public URL to ``http://127.0.0.1``);
* bodies are streamed and truncated at ``max_bytes`` so a huge page cannot
  exhaust memory;
* only text-ish content types are read - PDFs and binaries are reported as
  unsupported instead of being parsed blindly;
* scripts are never executed (extraction strips them);
* errors are returned as data, never raised to the caller as a 500, so one bad
  source cannot fail an entire research run.

``transport`` is injectable for tests (``httpx.MockTransport``), which keeps the
test suite offline and deterministic.
"""
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin

import httpx

from app.core.url_validation import UnsafeUrlError, assert_safe_destination
from app.models.research import RetrievalStatus
from app.services.html_extraction import ExtractedPage, extract_readable

READABLE_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")
UNSUPPORTED_CONTENT_TYPES = (
    "application/pdf",
    "application/zip",
    "application/octet-stream",
    "image/",
    "video/",
    "audio/",
)


@dataclass
class FetchResult:
    """Result of attempting to read one URL."""

    url: str
    status: RetrievalStatus
    final_url: Optional[str] = None
    http_status: Optional[int] = None
    content_type: Optional[str] = None
    text: Optional[str] = None
    page: Optional[ExtractedPage] = None
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == RetrievalStatus.FETCHED


def _content_type_allowed(content_type: Optional[str]) -> tuple[bool, str]:
    if not content_type:
        return True, "no content-type header"
    normalized = content_type.split(";")[0].strip().lower()
    if any(normalized.startswith(bad) for bad in UNSUPPORTED_CONTENT_TYPES):
        return False, f"unsupported content type: {normalized}"
    if any(normalized.startswith(good) for good in READABLE_CONTENT_TYPES):
        return True, normalized
    if normalized.startswith("text/"):
        return True, normalized
    return False, f"unsupported content type: {normalized}"


def _decode(body: bytes, charset: Optional[str]) -> str:
    for encoding in filter(None, [charset, "utf-8"]):
        try:
            return body.decode(encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


async def fetch_url(
    url: str,
    *,
    timeout_seconds: float = 12.0,
    max_bytes: int = 2_000_000,
    max_redirects: int = 3,
    transport: Optional[httpx.AsyncBaseTransport] = None,
) -> FetchResult:
    """Fetch and extract a single URL, returning a :class:`FetchResult`.

    Never raises for network/URL problems; inspect ``status``/``error`` instead.
    """
    notes: List[str] = []
    current_url = url

    try:
        timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 10.0))
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            headers={
                "User-Agent": "DocForge-Research/1.0 (+research citations; contact project owner)",
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.1",
            },
        ) as client:
            for _hop in range(max_redirects + 1):
                try:
                    normalized, _host, _addresses = await assert_safe_destination(current_url)
                except UnsafeUrlError as exc:
                    return FetchResult(
                        url=url,
                        status=RetrievalStatus.BLOCKED,
                        final_url=current_url,
                        error=str(exc),
                        notes=notes,
                    )

                try:
                    async with client.stream("GET", normalized) as response:
                        if response.status_code in (301, 302, 303, 307, 308):
                            location = response.headers.get("location")
                            if not location:
                                return FetchResult(
                                    url=url,
                                    status=RetrievalStatus.FAILED,
                                    final_url=normalized,
                                    http_status=response.status_code,
                                    error="Redirect without a Location header",
                                    notes=notes,
                                )
                            current_url = urljoin(normalized, location)
                            notes.append(f"Redirected (HTTP {response.status_code}) to another host; re-validating.")
                            continue

                        allowed, type_note = _content_type_allowed(response.headers.get("content-type"))
                        if not allowed:
                            return FetchResult(
                                url=url,
                                status=RetrievalStatus.UNSUPPORTED,
                                final_url=normalized,
                                http_status=response.status_code,
                                content_type=type_note,
                                error=type_note,
                                notes=notes,
                            )

                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > max_bytes:
                                notes.append(f"Response truncated at {max_bytes} bytes.")
                                break

                        content_type = response.headers.get("content-type", "")
                        charset = response.charset_encoding
                        text = _decode(bytes(body), charset)

                        page = None
                        if "html" in content_type.lower() or text.lstrip().startswith("<"):
                            page = extract_readable(text, str(response.url))
                            notes.extend(page.notes)

                        return FetchResult(
                            url=url,
                            status=RetrievalStatus.FETCHED,
                            final_url=str(response.url),
                            http_status=response.status_code,
                            content_type=content_type,
                            text=text,
                            page=page,
                            notes=notes,
                        )
                except httpx.TimeoutException:
                    return FetchResult(
                        url=url,
                        status=RetrievalStatus.FAILED,
                        final_url=current_url,
                        error=f"Timed out after {timeout_seconds:.0f}s",
                        notes=notes,
                    )
                except httpx.HTTPError as exc:
                    return FetchResult(
                        url=url,
                        status=RetrievalStatus.FAILED,
                        final_url=current_url,
                        error=f"Request failed: {type(exc).__name__}",
                        notes=notes,
                    )

            return FetchResult(
                url=url,
                status=RetrievalStatus.FAILED,
                final_url=current_url,
                error=f"Too many redirects (limit {max_redirects})",
                notes=notes,
            )
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # defensive: scheduler or connection pool errors
        return FetchResult(
            url=url,
            status=RetrievalStatus.FAILED,
            final_url=current_url,
            error=f"Unexpected fetch error: {type(exc).__name__}",
            notes=notes,
        )
