"""Score and rank candidate results for a lead.

The original picked the *first* result. We instead score every candidate in the
top-N by how well it matches the lead — name similarity, whether the URL is a
real personal LinkedIn profile, and whether the inferred company agrees with the
company we guessed from the e-mail — and pick the best. That's the core of the
"smarter" behaviour.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from .types import Candidate, ParsedProfile, SearchItem

__all__ = ["name_similarity", "score_candidate", "rank_candidates"]

_PROFILE_URL = re.compile(r"linkedin\.com/(in|pub)/", re.I)
_NONWORD = re.compile(r"[^a-z0-9]+")


def _norm(s: str) -> str:
    return _NONWORD.sub(" ", (s or "").lower()).strip()


def name_similarity(a: str, b: str) -> float:
    """0..1 similarity between two names, tolerant of token order/extra tokens."""
    ta, tb = set(_norm(a).split()), set(_norm(b).split())
    if not ta or not tb:
        return 0.0
    overlap = len(ta & tb) / len(ta | tb)                       # Jaccard on tokens
    ratio = SequenceMatcher(None, _norm(a), _norm(b)).ratio()    # char-level
    return max(overlap, ratio)


def score_candidate(cand: Candidate, name: str, company_guess: str | None) -> float:
    """Weighted 0..1 score for how well a candidate matches the lead."""
    item, parsed = cand.item, cand.parsed
    score = 0.0

    # name match — the strongest signal (weight 0.6)
    cand_name = parsed.name or item.title
    score += 0.6 * name_similarity(name, cand_name or "")

    # a real personal profile URL (weight 0.25)
    if _PROFILE_URL.search(item.link or ""):
        score += 0.25
    elif "linkedin.com" in (item.link or "").lower():
        score += 0.1

    # company agreement between e-mail guess and result (weight 0.15)
    if company_guess and parsed.company:
        cs = name_similarity(company_guess, parsed.company)
        score += 0.15 * cs

    return min(score, 1.0)


def rank_candidates(items, name, company_guess, parser):
    """Parse, score and sort candidate ``SearchItem``s best-first."""
    cands = []
    for it in items:
        parsed = parser(it.title, it.snippet, name)
        c = Candidate(item=it, parsed=parsed)
        c.score = score_candidate(c, name, company_guess)
        cands.append(c)
    cands.sort(key=lambda c: c.score, reverse=True)
    return cands
