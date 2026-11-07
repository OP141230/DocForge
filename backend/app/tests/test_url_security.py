"""URL validation and SSRF-guard tests.

No real DNS or network traffic: hosts are IP literals (public or private) and
HTTP is exercised with httpx.MockTransport.
"""
import httpx
import pytest

from app.core.url_validation import (
    UnsafeUrlError,
    assert_safe_destination,
    normalize_url,
    validate_url_syntax,
)
from app.models.research import RetrievalStatus
from app.services.source_fetcher import fetch_url


PUBLIC_IP_URL = "http://93.184.216.34/page"


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/file",
        "javascript:alert(1)",
        "http://localhost/admin",
        "http://127.0.0.1:80/",
        "http://[::1]/",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/internal",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://0.0.0.0/",
        "http://93.184.216.34:8080/other-port",
        "http://user:password@93.184.216.34/",
        "http://intranet/",
        "http://metadata.google.internal/",
        "http://printer.local/",
    ],
)
def test_blocks_dangerous_urls(url):
    with pytest.raises(UnsafeUrlError):
        validate_url_syntax(url)


def test_accepts_public_http_url():
    normalized, host = validate_url_syntax("HTTPS://Example.COM:443/path#frag")
    assert normalized == "https://example.com/path"
    assert host == "example.com"


def test_normalize_url_collapses_equivalent_forms():
    assert normalize_url("https://example.com/") == "https://example.com"
    assert normalize_url("https://example.com:443/a") == "https://example.com/a"


async def test_assert_safe_destination_rejects_private_literal():
    with pytest.raises(UnsafeUrlError):
        await assert_safe_destination("http://192.168.0.1/")


async def test_assert_safe_destination_accepts_public_literal():
    url, host, addresses = await assert_safe_destination(PUBLIC_IP_URL)
    assert url == PUBLIC_IP_URL
    assert addresses == ["93.184.216.34"]


async def test_fetch_extracts_readable_content():
    html = """
    <html><head>
      <title>Quarterly results</title>
      <meta name="author" content="Jane Doe">
      <meta property="article:published_time" content="2023-03-05">
      <meta property="og:site_name" content="World Institute">
    </head><body>
      <nav>menu</nav>
      <article>
        <p>The platform processed 42 percent of records in the first quarter of 2023.</p>
        <p>It was deployed across three regions and handled the workload reliably.</p>
      </article>
      <script>steal()</script>
    </body></html>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html"}, text=html)

    result = await fetch_url(PUBLIC_IP_URL, transport=httpx.MockTransport(handler))
    assert result.status == RetrievalStatus.FETCHED
    assert result.page is not None
    assert result.page.title == "Quarterly results"
    assert result.page.author == "Jane Doe"
    assert result.page.published_date == "2023-03-05"
    assert "42 percent" in result.page.text
    assert "steal" not in result.page.text
    assert "menu" not in result.page.text


async def test_fetch_blocks_redirect_to_private_address():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "http://127.0.0.1/api/auth/me"})

    result = await fetch_url(PUBLIC_IP_URL, transport=httpx.MockTransport(handler))
    assert result.status == RetrievalStatus.BLOCKED
    assert "non-public" in (result.error or "")


async def test_fetch_marks_unsupported_content_types():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "application/pdf"}, content=b"%PDF-1.4"
        )

    result = await fetch_url(PUBLIC_IP_URL, transport=httpx.MockTransport(handler))
    assert result.status == RetrievalStatus.UNSUPPORTED


async def test_fetch_truncates_oversized_pages():
    body = "<html><body>" + ("word " * 5000) + "</body></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html"}, text=body)

    result = await fetch_url(PUBLIC_IP_URL, max_bytes=500, transport=httpx.MockTransport(handler))
    assert result.status == RetrievalStatus.FETCHED
    assert any("truncated" in note.lower() for note in result.notes)


async def test_fetch_reports_timeouts_as_failed():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    result = await fetch_url(PUBLIC_IP_URL, transport=httpx.MockTransport(handler))
    assert result.status == RetrievalStatus.FAILED
    assert "timed out" in (result.error or "").lower()


async def test_fetch_reports_too_many_redirects():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": PUBLIC_IP_URL + "?loop=1"})

    result = await fetch_url(
        PUBLIC_IP_URL, max_redirects=2, transport=httpx.MockTransport(handler)
    )
    assert result.status == RetrievalStatus.FAILED
    assert "redirect" in (result.error or "").lower()
