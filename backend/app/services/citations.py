"""Citation formatting for APA 7, IEEE, MLA 9 and Chicago author-date.

Design principles
-----------------
1. **Never invent metadata.** Missing author/date/publisher are omitted (or
   rendered as ``n.d.`` where the style requires a placeholder) rather than
   guessed. A citation that looks complete but is fabricated is worse than one
   with visible gaps.
2. **Pure functions.** Formatting takes a :class:`CitationSource` value object and
   returns a string. No database access, which makes every style unit-testable
   and lets the API render a reference list in any style on demand.
3. **Plain text.** DocForge's Document IR stores plain text runs, so italics and
   quotation-mark conventions are approximated with text (titles are quoted for
   article-like sources, unquoted for standalone works). Documented limitation.

Extending: add a function ``_format_<style>``, register it in ``_FORMATTERS`` and
``_IN_TEXT_FORMATTERS``, and add the value to ``CitationStyle``.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from app.models.research import CitationStyle

MONTHS_FULL = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTHS_ABBR = [
    "Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.",
    "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.",
]

STYLE_LABELS = {
    CitationStyle.APA: "APA 7th edition",
    CitationStyle.IEEE: "IEEE",
    CitationStyle.MLA: "MLA 9th edition",
    CitationStyle.CHICAGO: "Chicago author-date",
}

SUPPORTED_STYLES = list(STYLE_LABELS.keys())


@dataclass
class CitationSource:
    """Everything a formatter is allowed to use about one source."""

    source_id: str
    title: Optional[str] = None
    authors: List[str] = None            # type: ignore[assignment]
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    accessed_at: Optional[datetime] = None
    source_type: str = "web"             # web | knowledge_base | user_url
    site_name: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    def __post_init__(self) -> None:
        if self.authors is None:
            self.authors = []

    @property
    def is_uploaded_document(self) -> bool:
        return self.source_type == "knowledge_base"

    @property
    def display_title(self) -> str:
        title = (self.title or "").strip()
        return title or "Untitled source"

    @property
    def link(self) -> Optional[str]:
        """Preferred link: DOI first (more stable), then the URL."""
        if self.doi:
            doi = self.doi.strip()
            if doi.lower().startswith("http"):
                return doi
            return f"https://doi.org/{doi.lstrip('doi:').strip()}"
        if self.url and re.match(r"^https?://", self.url.strip(), re.IGNORECASE):
            return self.url.strip()
        return None


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def parse_year(value: Optional[str]) -> Optional[str]:
    """Return a 4-digit year found in ``value`` or ``None``."""
    if not value:
        return None
    match = re.search(r"\b(1[89]\d{2}|20\d{2})\b", str(value))
    return match.group(1) if match else None


def _parse_date_parts(value: Optional[str]) -> Optional[Tuple[int, int, int]]:
    """Parse an ISO-ish date into ``(year, month, day)``."""
    if not value:
        return None
    text = str(value).strip()
    iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso:
        try:
            year, month, day = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
            if 1 <= month <= 12 and 1 <= day <= 31:
                return year, month, day
        except ValueError:
            pass
    year = parse_year(text)
    if year:
        return int(year), 0, 0
    return None


def _apa_date(value: Optional[str]) -> str:
    parts = _parse_date_parts(value)
    if not parts:
        return "n.d."
    year, month, day = parts
    if month and day:
        return f"{year}, {MONTHS_FULL[month - 1]} {day}"
    if month:
        return f"{year}, {MONTHS_FULL[month - 1]}"
    return str(year)


def _ieee_date(value: Optional[str]) -> Optional[str]:
    parts = _parse_date_parts(value)
    if not parts:
        return None
    year, month, day = parts
    if month and day:
        return f"{MONTHS_ABBR[month - 1]} {day}, {year}"
    if month:
        return f"{MONTHS_ABBR[month - 1]} {year}"
    return str(year)


def _mla_date(value: Optional[str]) -> Optional[str]:
    parts = _parse_date_parts(value)
    if not parts:
        return None
    year, month, day = parts
    if month and day:
        return f"{day} {MONTHS_ABBR[month - 1]} {year}"
    if month:
        return f"{MONTHS_ABBR[month - 1]} {year}"
    return str(year)


def _accessed_mla(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    return f"{value.day} {MONTHS_ABBR[value.month - 1]} {value.year}"


# ---------------------------------------------------------------------------
# Author formatting
# ---------------------------------------------------------------------------

def _split_name(name: str) -> Tuple[str, str]:
    """Return ``(surname, given)`` from ``"Jane Q. Doe"`` or ``"Doe, Jane Q."``."""
    cleaned = " ".join(str(name).replace("\n", " ").split()).strip()
    if not cleaned:
        return "", ""
    if "," in cleaned:
        surname, given = cleaned.split(",", 1)
        return surname.strip(), given.strip()
    tokens = cleaned.split(" ")
    if len(tokens) == 1:
        return tokens[0], ""
    return tokens[-1], " ".join(tokens[:-1])


def _initials(given: str) -> str:
    parts = [p for p in re.split(r"[\s.]+", given) if p]
    return " ".join(f"{part[0].upper()}." for part in parts)


def _apa_authors(authors: List[str]) -> Optional[str]:
    if not authors:
        return None
    formatted: List[str] = []
    for name in authors[:20]:
        surname, given = _split_name(name)
        if not surname:
            continue
        initials = _initials(given)
        formatted.append(f"{surname}, {initials}".strip().rstrip(","))
    if not formatted:
        return None
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return ", ".join(formatted[:19]) + ", . . . " + formatted[-1]


def _ieee_authors(authors: List[str]) -> Optional[str]:
    if not authors:
        return None
    formatted: List[str] = []
    for name in authors:
        surname, given = _split_name(name)
        if not surname:
            continue
        initials = _initials(given)
        formatted.append(f"{initials} {surname}".strip())
    if not formatted:
        return None
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    return ", ".join(formatted[:-1]) + ", and " + formatted[-1]


def _mla_authors(authors: List[str]) -> Optional[str]:
    if not authors:
        return None
    first_surname, first_given = _split_name(authors[0])
    if not first_surname:
        return None
    first = f"{first_surname}, {first_given}".strip().rstrip(",")
    if len(authors) == 1:
        return first
    rest = []
    for name in authors[1:3]:
        surname, given = _split_name(name)
        rest.append(f"{given} {surname}".strip())
    if len(authors) >= 3:
        return f"{first}, et al."
    return f"{first}, and {rest[0]}"


def _chicago_authors(authors: List[str]) -> Optional[str]:
    if not authors:
        return None
    surname, given = _split_name(authors[0])
    if not surname:
        return None
    first = f"{surname}, {given}".strip().rstrip(",")
    if len(authors) == 1:
        return first
    if len(authors) == 2:
        s2, g2 = _split_name(authors[1])
        return f"{first}, and {g2} {s2}".strip()
    s2, g2 = _split_name(authors[1])
    return f"{first}, {g2} {s2}, et al."


def _short_title(source: CitationSource, limit: int = 40) -> str:
    title = source.display_title
    if len(title) <= limit:
        return title
    return title[: limit - 1].rstrip() + "…"


def _sentence_title(title: str) -> str:
    """APA capitalizes only the first word of a title (sentence case)."""
    return title[:1].upper() + title[1:] if title else title


def _ensure_period(text: Optional[str]) -> str:
    """Append a single period, never a second one."""
    value = (text or "").strip()
    if not value:
        return ""
    return value if value.endswith(".") else value + "."


# ---------------------------------------------------------------------------
# Reference-list formatting
# ---------------------------------------------------------------------------

def _format_apa(source: CitationSource, index: int) -> str:
    if source.is_uploaded_document:
        return f"{source.display_title}. (n.d.). Uploaded document, DocForge knowledge base."

    authors = _apa_authors(source.authors)
    date = _apa_date(source.published_date)
    title = _sentence_title(source.display_title)
    parts: List[str] = []

    if authors:
        parts.append(f"{_ensure_period(authors)} ({date}). {title}.")
    else:
        parts.append(f"{title}. ({date}).")

    if source.site_name:
        parts.append(f"{source.site_name}.")
    elif source.publisher:
        parts.append(f"{source.publisher}.")

    if source.link:
        parts.append(source.link)
    elif source.accessed_at and not parse_year(source.published_date):
        parts.append(
            f"Retrieved {MONTHS_FULL[source.accessed_at.month - 1]} "
            f"{source.accessed_at.day}, {source.accessed_at.year}."
        )

    return " ".join(parts)


def _format_ieee(source: CitationSource, index: int) -> str:
    if source.is_uploaded_document:
        return (
            f'[{index}] "{source.display_title}," uploaded document, '
            f"DocForge knowledge base."
        )

    authors = _ieee_authors(source.authors)
    date = _ieee_date(source.published_date)
    venue = source.site_name or source.publisher

    # IEEE puts the comma inside the quotation marks: "Title," Journal, 2023.
    entry = f"[{index}] "
    if authors:
        entry += f"{authors}, "
    entry += f'"{source.display_title},"'

    if venue and date:
        entry += f" {venue}, {date}."
    elif venue:
        entry += f" {venue}."
    elif date:
        entry += f" {date}."

    if source.link:
        entry += f" [Online]. Available: {source.link}."
    if source.accessed_at:
        entry += f" [Accessed: {_ieee_date(source.accessed_at.date().isoformat())}]."
    return entry


def _format_mla(source: CitationSource, index: int) -> str:
    if source.is_uploaded_document:
        return (
            f'"{source.display_title}." Uploaded document, '
            f"DocForge knowledge base."
        )

    authors = _mla_authors(source.authors)
    title = f'"{source.display_title}."'
    parts: List[str] = []

    parts.append(f"{authors}. {title}" if authors else title)

    venue = source.site_name or source.publisher
    if venue:
        parts.append(f"{venue},")

    date = _mla_date(source.published_date)
    if date:
        parts.append(f"{date},")

    if source.link:
        parts.append(f"{source.link}.")

    accessed = _accessed_mla(source.accessed_at)
    if accessed:
        parts.append(f"Accessed {accessed}.")

    text = " ".join(parts).strip()
    text = re.sub(r",\s*$", ".", text)
    return text if text.endswith(".") else text + "."


def _format_chicago(source: CitationSource, index: int) -> str:
    if source.is_uploaded_document:
        return (
            f'"{source.display_title}." n.d. Uploaded document, '
            f"DocForge knowledge base."
        )

    authors = _chicago_authors(source.authors)
    year = parse_year(source.published_date) or "n.d."
    year_part = _ensure_period(year)
    title = f'"{source.display_title}."'

    if authors:
        entry = f"{_ensure_period(authors)} {year_part} {title}"
    else:
        entry = f"{title} {year_part}"

    venue = source.site_name or source.publisher
    if venue:
        entry += f" {venue}."
    if source.link:
        entry += f" {source.link}."
    return entry


_FORMATTERS: Dict[CitationStyle, Callable[[CitationSource, int], str]] = {
    CitationStyle.APA: _format_apa,
    CitationStyle.IEEE: _format_ieee,
    CitationStyle.MLA: _format_mla,
    CitationStyle.CHICAGO: _format_chicago,
}


def normalize_style(style: Optional[str | CitationStyle]) -> CitationStyle:
    """Accept ``"apa"``, ``"APA"``, ``"apa7"`` etc.; default to APA."""
    if isinstance(style, CitationStyle):
        return style
    if not style:
        return CitationStyle.APA
    value = str(style).strip().lower().replace("-", "").replace("_", "")
    mapping = {
        "apa": CitationStyle.APA,
        "apa7": CitationStyle.APA,
        "apa7thedition": CitationStyle.APA,
        "ieee": CitationStyle.IEEE,
        "mla": CitationStyle.MLA,
        "mla9": CitationStyle.MLA,
        "chicago": CitationStyle.CHICAGO,
        "chicagoauthordate": CitationStyle.CHICAGO,
    }
    if value not in mapping:
        raise ValueError(
            f"Unsupported citation style '{style}'. Supported: "
            f"{', '.join(s.value for s in SUPPORTED_STYLES)}"
        )
    return mapping[value]


def format_reference(
    source: CitationSource,
    style: str | CitationStyle = CitationStyle.APA,
    index: int = 1,
) -> str:
    """Render one reference-list entry."""
    normalized = normalize_style(style)
    return _FORMATTERS[normalized](source, index)


# ---------------------------------------------------------------------------
# In-text formatting
# ---------------------------------------------------------------------------

def _in_text_apa(source: CitationSource, index: int, locator: Optional[str]) -> str:
    year = parse_year(source.published_date) or "n.d."
    if source.authors:
        surnames = [_split_name(name)[0] for name in source.authors if _split_name(name)[0]]
        if not surnames:
            name_part = f'"{_short_title(source)}"'
        elif len(surnames) == 1:
            name_part = surnames[0]
        elif len(surnames) == 2:
            name_part = f"{surnames[0]} & {surnames[1]}"
        else:
            name_part = f"{surnames[0]} et al."
    else:
        name_part = f'"{_short_title(source)}"'

    suffix = f", {_locator_apa(locator)}" if locator else ""
    return f"({name_part}, {year}{suffix})"


def _locator_apa(locator: str) -> str:
    cleaned = str(locator).strip()
    if re.match(r"^(p|pp|para|sec|fig|chap)\.?\s", cleaned, re.IGNORECASE):
        return cleaned
    return f"p. {cleaned}"


def _in_text_mla(source: CitationSource, index: int, locator: Optional[str]) -> str:
    if source.authors:
        first = _split_name(source.authors[0])[0]
        name_part = f"{first} et al." if len(source.authors) > 2 else first
    else:
        name_part = f'"{_short_title(source)}"'
    return f"({name_part} {locator})" if locator else f"({name_part})"


def _in_text_chicago(source: CitationSource, index: int, locator: Optional[str]) -> str:
    year = parse_year(source.published_date) or "n.d."
    if source.authors:
        surname = _split_name(source.authors[0])[0]
        name_part = f"{surname} et al." if len(source.authors) > 2 else surname
    else:
        name_part = f'"{_short_title(source)}"'
    if locator:
        return f"({name_part} {year}, {locator})"
    return f"({name_part} {year})"


def _in_text_ieee(source: CitationSource, index: int, locator: Optional[str]) -> str:
    if locator:
        return f"[{index}, {locator}]"
    return f"[{index}]"


_IN_TEXT: Dict[CitationStyle, Callable[[CitationSource, int, Optional[str]], str]] = {
    CitationStyle.APA: _in_text_apa,
    CitationStyle.IEEE: _in_text_ieee,
    CitationStyle.MLA: _in_text_mla,
    CitationStyle.CHICAGO: _in_text_chicago,
}


def format_in_text(
    source: CitationSource,
    style: str | CitationStyle = CitationStyle.APA,
    index: int = 1,
    locator: Optional[str] = None,
) -> str:
    """Render an in-text citation marker."""
    normalized = normalize_style(style)
    return _IN_TEXT[normalized](source, index, locator)


def source_sort_key(source: CitationSource) -> str:
    """Alphabetical key for APA/MLA/Chicago reference lists."""
    if source.authors:
        surname = _split_name(source.authors[0])[0]
        if surname:
            return surname.lower()
    return source.display_title.lower()
