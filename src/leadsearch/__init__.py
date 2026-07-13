"""leadsearch — enrich (name, e-mail) leads with job title, workplace & LinkedIn.

A smarter Python successor to the R package: e-mail intelligence (company /
name / account-type inference), robust multi-format LinkedIn parsing, and
candidate scoring/ranking instead of "first result wins".

    from leadsearch import LeadSearch, GoogleProvider

    ls = LeadSearch(GoogleProvider(api_key="...", cx="..."))
    leads = ls.enrich([("Jane Doe", "jane@acme.com"), ("John", "john@gmail.com")])
    for lead in leads:
        print(lead.as_dict())
"""

from __future__ import annotations

from .cache import Cache, CachingProvider, JSONFileCache, MemoryCache
from .core import LeadSearch, build_query
from .domain_intel import DomainInfo, analyze_domain
from .email_intel import analyze_email, company_from_domain, name_from_local
from .parse import parse_linkedin
from .providers import BingProvider, GoogleProvider, MockProvider, Provider
from .scoring import name_similarity, rank_candidates, score_candidate
from .types import Candidate, EmailInfo, Lead, ParsedProfile, SearchItem

__version__ = "0.2.0"

__all__ = [
    "LeadSearch", "build_query",
    "GoogleProvider", "BingProvider", "MockProvider", "Provider",
    "CachingProvider", "Cache", "MemoryCache", "JSONFileCache",
    "analyze_email", "company_from_domain", "name_from_local",
    "analyze_domain", "DomainInfo",
    "parse_linkedin", "name_similarity", "score_candidate", "rank_candidates",
    "Lead", "EmailInfo", "ParsedProfile", "SearchItem", "Candidate",
    "__version__",
]
