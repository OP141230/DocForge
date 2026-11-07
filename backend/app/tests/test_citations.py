"""Citation formatting tests (APA 7, IEEE, MLA 9, Chicago author-date)."""
from datetime import datetime

import pytest

from app.models.research import CitationStyle
from app.services.citations import (
    CitationSource,
    format_in_text,
    format_reference,
    normalize_style,
    parse_year,
)


def make_source(**overrides) -> CitationSource:
    defaults = dict(
        source_id="src-1",
        title="Climate report",
        authors=["Jane Doe"],
        publisher="World Institute",
        published_date="2023-03-05",
        url="https://example.org/report",
        site_name="World Institute",
        accessed_at=datetime(2024, 3, 5),
    )
    defaults.update(overrides)
    return CitationSource(**defaults)


def test_apa_reference_with_author_and_date():
    text = format_reference(make_source(), CitationStyle.APA)
    assert text == (
        "Doe, J. (2023, March 5). Climate report. World Institute. "
        "https://example.org/report"
    )


def test_apa_reference_without_author_starts_with_title():
    text = format_reference(make_source(authors=[]), CitationStyle.APA)
    assert text.startswith("Climate report. (2023, March 5).")
    # No invented author, and the date is the real one.
    assert "Doe" not in text


def test_apa_reference_uses_n_d_when_date_is_missing():
    text = format_reference(make_source(published_date=None), CitationStyle.APA)
    assert "(n.d.)" in text


def test_apa_reference_multiple_authors_uses_ampersand():
    text = format_reference(make_source(authors=["Jane Doe", "Rick Roe"]), CitationStyle.APA)
    assert "Doe, J., & Roe, R." in text


def test_ieee_reference_is_numbered_and_quotes_title():
    text = format_reference(make_source(), CitationStyle.IEEE, index=3)
    assert text.startswith('[3] J. Doe, "Climate report," World Institute, Mar. 5, 2023.')
    assert "Available: https://example.org/report" in text
    assert "Accessed: Mar. 5, 2024" in text


def test_ieee_reference_omits_missing_year_instead_of_guessing():
    text = format_reference(make_source(published_date=None), CitationStyle.IEEE)
    assert "n.d." not in text
    assert "2023" not in text


def test_mla_reference_uses_day_month_year():
    text = format_reference(make_source(), CitationStyle.MLA)
    assert 'Doe, Jane. "Climate report."' in text
    assert "5 Mar. 2023" in text
    assert "Accessed 5 Mar. 2024" in text


def test_chicago_reference_uses_author_date_order():
    text = format_reference(make_source(), CitationStyle.CHICAGO)
    assert text.startswith('Doe, Jane. 2023. "Climate report."')
    assert "n.d." not in text


def test_chicago_uses_n_d_placeholder_without_date():
    text = format_reference(make_source(published_date=None), CitationStyle.CHICAGO)
    assert " n.d. " in text


def test_uploaded_document_is_labelled_as_such():
    text = format_reference(
        make_source(
            title="notes.txt",
            authors=[],
            publisher="Uploaded document",
            published_date=None,
            url=None,
            source_type="knowledge_base",
            site_name=None,
        ),
        CitationStyle.APA,
    )
    assert "notes.txt" in text
    assert "Uploaded document" in text
    assert "https://" not in text


def test_missing_metadata_is_not_invented():
    """A source with almost nothing must not gain fake authors or URLs."""
    text = format_reference(
        CitationSource(source_id="bare", title="Untitled memo", authors=[]),
        CitationStyle.APA,
    )
    assert "Untitled memo" in text
    assert "(n.d.)" in text
    assert "https://" not in text
    assert "doi" not in text.lower()


def test_doi_is_preferred_over_url():
    text = format_reference(
        make_source(doi="10.1000/xyz123"), CitationStyle.APA
    )
    assert "https://doi.org/10.1000/xyz123" in text
    assert "example.org" not in text


@pytest.mark.parametrize(
    "style,expected",
    [
        (CitationStyle.APA, "(Doe, 2023)"),
        (CitationStyle.IEEE, "[1]"),
        (CitationStyle.MLA, "(Doe)"),
        (CitationStyle.CHICAGO, "(Doe 2023)"),
    ],
)
def test_in_text_citations(style, expected):
    assert format_in_text(make_source(), style, index=1) == expected


def test_in_text_apa_three_authors_uses_et_al():
    source = make_source(authors=["Jane Doe", "Rick Roe", "Sam Poe"])
    assert format_in_text(source, CitationStyle.APA) == "(Doe et al., 2023)"


def test_in_text_locator_is_rendered():
    assert format_in_text(make_source(), CitationStyle.IEEE, index=2, locator="12") == "[2, 12]"
    assert format_in_text(make_source(), CitationStyle.APA, locator="12") == "(Doe, 2023, p. 12)"


def test_normalize_style_accepts_aliases():
    assert normalize_style("APA") == CitationStyle.APA
    assert normalize_style("mla9") == CitationStyle.MLA
    assert normalize_style("chicago-author-date") == CitationStyle.CHICAGO
    with pytest.raises(ValueError):
        normalize_style("harvard")


def test_parse_year():
    assert parse_year("2023-03-05") == "2023"
    assert parse_year("March 2021") == "2021"
    assert parse_year(None) is None
    assert parse_year("no year here") is None
