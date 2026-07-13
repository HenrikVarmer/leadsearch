"""Parse a LinkedIn search result into name / title / company.

LinkedIn result titles come in several shapes:

    "Jane Doe - Head of Data & AI - Acme | LinkedIn"
    "Jane Doe - Head of Data at Acme | LinkedIn"
    "Jane Doe – Acme – Head of Data | LinkedIn"
    "Jane Doe - Head of Data | LinkedIn"   (company only in the snippet)

The original R port split the title on a single pattern. This handles the common
variants and falls back to the result snippet for the company when the title
doesn't carry it.
"""

from __future__ import annotations

import re

from .types import ParsedProfile

__all__ = ["parse_linkedin"]

_DASHES = re.compile(r"\s+[-–—|]\s+")
_TRAILER = re.compile(r"\s*[|\-–—]\s*linkedin.*$", re.I)
_AT = re.compile(r"\s+\bat\b\s+", re.I)


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip(" -–—|")


def parse_linkedin(title: str, snippet: str = "", name: str | None = None) -> ParsedProfile:
    """Best-effort parse of a LinkedIn result's title (+ snippet) into parts."""
    raw = _TRAILER.sub("", title or "").strip()
    prof = ParsedProfile()

    # "<Title> at <Company>" anywhere in the title
    segments = [_clean(s) for s in _DASHES.split(raw) if _clean(s)]
    if not segments:
        segments = [_clean(raw)] if _clean(raw) else []

    # first segment is usually the person's name
    if segments:
        prof.name = segments[0]
        rest = segments[1:]
    else:
        rest = []

    # look for "Title at Company" in any remaining segment
    for seg in rest:
        m = _AT.search(seg)
        if m:
            prof.title = _clean(seg[: m.start()])
            prof.company = _clean(seg[m.end():])
            break
    else:
        # otherwise: [Title, Company] or just [Title]
        if len(rest) >= 2:
            prof.title, prof.company = rest[0], rest[1]
        elif len(rest) == 1:
            prof.title = rest[0]

    # snippet fallback for company: "... at Acme. ..." / "Company · Location"
    if not prof.company and snippet:
        m = _AT.search(snippet)
        if m:
            tail = snippet[m.end():]
            prof.company = _clean(re.split(r"[.·|,\n]", tail)[0])[:80] or None

    # if the "title" is really the company (e.g. "Jane – Acme – Head of Data")
    if prof.title and prof.company is None and name and prof.title.lower() == (name or "").lower():
        prof.title = None

    return prof
