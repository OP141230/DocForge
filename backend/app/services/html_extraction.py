"""Readable-content extraction for web pages (Phase 5).

Search snippets are not evidence: a snippet is a few words chosen by the search
engine, so verification built on snippets would be close to guesswork. This
module turns a fetched page into (a) plain text and (b) paragraph-sized
passages that can be quoted back to the user with a source link.

Only metadata that actually appears on the page is captured. If there is no
publication date, ``published_date`` stays ``None`` - we never invent one, and
the citation formatter prints "n.d." instead.

Scripts are never executed: ``script``/``style``/``noscript`` nodes are removed
before text extraction, and the fetcher refuses non-text content types.
"""
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

REMOVED_TAGS = (
    "script", "style", "noscript", "iframe", "svg", "canvas", "form",
    "nav", "header", "footer", "aside", "button", "input", "select",
)

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

MAX_PASSAGE_CHARS = 1200


@dataclass
class ExtractedPassage:
    """A paragraph-sized excerpt with optional structural context."""

    text: str
    section_title: Optional[str] = None


@dataclass
class ExtractedPage:
    """Structured result of reading a web page."""

    title: str
    text: str
    canonical_url: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    source_type_label: str = "unknown"
    passages: List[ExtractedPassage] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def _meta(soup: BeautifulSoup, *, name: Optional[str] = None, prop: Optional[str] = None) -> Optional[str]:
    """Read a meta tag without trusting it blindly."""
    attrs: Dict[str, str] = {}
    if name:
        attrs["name"] = name
    if prop:
        attrs["property"] = prop
    if not attrs:
        return None

    tag = soup.find("meta", attrs=attrs)
    if not tag:
        return None
    value = tag.get("content")
    if not value:
        return None
    value = str(value).strip()
    return value[:1000] or None


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def _date_from_json_ld(soup: BeautifulSoup) -> Optional[str]:
    """Look for ``datePublished`` in JSON-LD blocks (no execution, just parsing)."""
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw or "datePublished" not in raw:
            continue
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            continue

        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                value = item.get("datePublished") or item.get("dateCreated")
                if isinstance(value, str):
                    match = DATE_PATTERN.search(value)
                    if match:
                        return match.group(0)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)

    return None


def _clean_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    match = DATE_PATTERN.search(value)
    if match:
        return match.group(0)
    year = YEAR_PATTERN.search(value)
    if year:
        return year.group(0)
    return None


def _label_source(soup: BeautifulSoup, url: str) -> str:
    """Heuristic classification. Shown to users as a hint, not a verdict."""
    host = (urlsplit(url).hostname or "").lower()
    if _meta(soup, name="citation_title") or _meta(soup, name="citation_journal_title"):
        return "peer_reviewed"
    if host.endswith(".gov") or ".gov." in host:
        return "government"
    if host.endswith(".edu") or ".edu." in host:
        return "academic"
    if any(part in host for part in ("arxiv.org", "doi.org", "pubmed", "nature.com", "ieee.org", "acm.org")):
        return "peer_reviewed"
    if any(part in host for part in ("docs.", "developer.", "readthedocs", "wikipedia.org")):
        return "reference"
    if _meta(soup, prop="article:published_time") or _meta(soup, name="news_keywords"):
        return "news"
    if host.startswith("blog.") or "/blog" in url:
        return "blog"
    return "unknown"


def build_passages(
    text: str,
    *,
    min_chars: int = 120,
    max_chars: int = MAX_PASSAGE_CHARS,
    section_title: Optional[str] = None,
) -> List[ExtractedPassage]:
    """Split text into paragraph-level passages of a usable size.

    Short lines are merged with neighbours so a passage is substantial enough to
    verify a claim against, but never merged past ``max_chars``.
    """
    blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
    passages: List[ExtractedPassage] = []
    buffer = ""

    def flush() -> None:
        nonlocal buffer
        if buffer.strip():
            passages.append(ExtractedPassage(text=buffer.strip(), section_title=section_title))
        buffer = ""

    for block in blocks:
        if len(block) > max_chars:
            # Split long paragraphs on sentence boundaries.
            sentences = re.split(r"(?<=[.!?])\s+", block)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) + 1 > max_chars and current:
                    passages.append(ExtractedPassage(text=current.strip(), section_title=section_title))
                    current = sentence
                else:
                    current = f"{current} {sentence}".strip()
            if len(current) >= min_chars:
                passages.append(ExtractedPassage(text=current.strip(), section_title=section_title))
            continue

        if len(buffer) + len(block) + 2 <= max_chars:
            buffer = f"{buffer}\n\n{block}".strip() if buffer else block
        else:
            flush()
            buffer = block

        if len(buffer) >= min_chars:
            flush()

    flush()
    return [p for p in passages if len(p.text) >= min_chars] or [
        ExtractedPassage(text=text[:max_chars], section_title=section_title)
    ] if text.strip() else []


def extract_readable(html: str, url: str) -> ExtractedPage:
    """Extract title, metadata, text and passages from an HTML document."""
    notes: List[str] = []

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:  # lxml missing or malformed markup
        soup = BeautifulSoup(html, "html.parser")
        notes.append("Parsed with the slower built-in parser (lxml unavailable).")

    for tag in soup.find_all(REMOVED_TAGS):
        tag.decompose()

    # Title: og:title > <title> > first h1
    title = _meta(soup, prop="og:title") or _meta(soup, name="twitter:title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        heading = soup.find("h1")
        title = heading.get_text(strip=True) if heading else urlsplit(url).hostname or url
    title = _normalize_whitespace(title)[:500]

    canonical = None
    link = soup.find("link", rel=lambda value: value and "canonical" in value)
    if link and link.get("href"):
        try:
            canonical = urljoin(url, str(link["href"]))
        except ValueError:
            canonical = None

    author = (
        _meta(soup, name="author")
        or _meta(soup, name="citation_author")
        or _meta(soup, prop="article:author")
    )
    publisher = (
        _meta(soup, prop="og:site_name")
        or _meta(soup, name="publisher")
        or _meta(soup, name="citation_journal_title")
        or _meta(soup, name="application-name")
    )
    if not publisher:
        publisher = urlsplit(url).hostname
        notes.append("Publisher inferred from the site hostname.")

    published = _clean_date(
        _meta(soup, prop="article:published_time")
        or _meta(soup, name="article:published_time")
        or _meta(soup, name="citation_publication_date")
        or _meta(soup, name="date")
        or _meta(soup, name="pubdate")
        or _date_from_json_ld(soup)
    )
    if not published:
        notes.append("No publication date found on the page.")

    # Prefer the article/main body to avoid navigation clutter.
    root = soup.find("article") or soup.find("main") or soup.body or soup
    text = _normalize_whitespace(root.get_text("\n"))

    if len(text) < 200:
        notes.append("Very little readable text was extracted from this page.")

    passages = build_passages(text)
    return ExtractedPage(
        title=title,
        text=text,
        canonical_url=canonical,
        author=author,
        publisher=publisher,
        published_date=published,
        source_type_label=_label_source(soup, url),
        passages=passages,
        notes=notes,
    )
