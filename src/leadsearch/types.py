"""Shared data types for :mod:`leadsearch`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmailInfo:
    """What we can infer about a lead from their e-mail alone."""

    email: str
    local: str
    domain: str
    is_free: bool = False        # gmail / hotmail / ... — company carries no signal
    is_role: bool = False        # info@ / sales@ / hr@ — not a person
    is_disposable: bool = False  # throwaway inbox
    company_guess: Optional[str] = None   # inferred from the domain
    name_guess: Optional[str] = None      # inferred from the local part


@dataclass
class SearchItem:
    """One result item from a search provider."""

    title: str = ""
    link: str = ""
    snippet: str = ""


@dataclass
class ParsedProfile:
    """A LinkedIn result parsed into its parts."""

    name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None


@dataclass
class Candidate:
    """A scored search result for a lead."""

    item: SearchItem
    parsed: ParsedProfile
    score: float = 0.0


@dataclass
class Lead:
    """An enriched lead — the output of :meth:`LeadSearch.enrich`."""

    name: str
    email: str
    title: str = "No Result"
    workplace: str = "No Result"
    link: str = "No Result"
    confidence: float = 0.0
    is_role_account: bool = False
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "title": self.title,
            "workplace": self.workplace,
            "link": self.link,
            "confidence": round(self.confidence, 3),
            "is_role_account": self.is_role_account,
            "notes": list(self.notes),
        }
