"""The LeadSearch pipeline — enrich (name, e-mail) leads with job info.

For each lead it: analyses the e-mail, builds the strongest query it can
(company-qualified when the domain carries signal, name-only otherwise), asks
the provider for the top-N results, parses + scores + ranks them, and returns
the best match with a confidence score. Role/free/disposable accounts are
flagged in ``notes``.
"""

from __future__ import annotations

from typing import Iterable, Optional, Union

from .domain_intel import analyze_domain
from .email_intel import analyze_email
from .parse import parse_linkedin
from .providers import Provider
from .scoring import rank_candidates
from .types import Lead

__all__ = ["LeadSearch", "build_query"]

LeadInput = Union[tuple, list, dict]


def build_query(name: str, company: Optional[str], *, site: str = "linkedin.com") -> str:
    """Build a search query, adding the company only when it carries signal."""
    q = f'site:{site} "{name}"' if name else f"site:{site}"
    if company:
        q += f" {company}"
    return q


class LeadSearch:
    """Enrich leads with job title, workplace and LinkedIn profile.

    Parameters
    ----------
    provider:
        A :class:`~leadsearch.providers.Provider` (Google, Bing or Mock).
    num:
        How many results to consider per query (ranked, not just the first).
    min_confidence:
        Results below this score are treated as "No Result".
    """

    def __init__(self, provider: Provider, *, num: int = 5, min_confidence: float = 0.35,
                 mx_lookup=None):
        self.provider = provider
        self.num = num
        self.min_confidence = min_confidence
        self.mx_lookup = mx_lookup   # optional domain -> [mx_host] for MX intelligence

    # -- single lead --------------------------------------------------------
    def enrich_one(self, name: str, email: str) -> Lead:
        info = analyze_email(email)
        # fall back to a name inferred from the address if none was supplied
        name = (name or "").strip() or (info.name_guess or "")
        lead = Lead(name=name or "(unknown)", email=email)

        # MX intelligence: a deliverable custom domain is a real company, even
        # when the plain-domain heuristic couldn't name it.
        if self.mx_lookup is not None and info.domain:
            dinfo = analyze_domain(info.domain, self.mx_lookup)
            if not dinfo.deliverable:
                lead.notes.append("domain has no MX record (may be undeliverable)")
            elif dinfo.provider:
                lead.notes.append(f"mail hosted on {dinfo.provider}")
            if dinfo.is_corporate and not info.company_guess:
                info.company_guess = dinfo.company_guess

        if info.is_disposable:
            lead.notes.append("disposable email")
        if info.is_role:
            lead.is_role_account = True
            lead.notes.append("role account (not a person)")
        if info.is_free:
            lead.notes.append("free mail — company not used in query")

        if not name:
            lead.notes.append("no name available")
            return lead

        # company-qualified query first, then a name-only fallback
        queries = []
        if info.company_guess:
            queries.append(build_query(name, info.company_guess))
        queries.append(build_query(name, None))

        best = None
        for q in queries:
            items = self.provider.search(q, self.num) or []
            cands = rank_candidates(items, name, info.company_guess, parse_linkedin)
            if cands and (best is None or cands[0].score > best.score):
                best = cands[0]
            if best and best.score >= 0.75:   # strong hit — stop early
                break

        if best is None or best.score < self.min_confidence:
            if best is not None:
                lead.notes.append(f"weak match discarded (score {best.score:.2f})")
            return lead

        p = best.parsed
        lead.title = p.title or "No Result"
        lead.workplace = p.company or info.company_guess or "No Result"
        lead.link = best.item.link or "No Result"
        lead.confidence = best.score
        return lead

    # -- batch --------------------------------------------------------------
    def enrich(self, leads: Iterable[LeadInput], workers: int = 1) -> list[Lead]:
        """Enrich an iterable of leads, optionally in parallel.

        Each lead may be a ``(name, email)`` pair or a mapping with ``name`` and
        ``email`` (or ``mail``) keys. Set ``workers > 1`` to enrich concurrently
        with a thread pool (I/O-bound search calls parallelise well); output
        order matches input order.
        """
        rows = [_unpack(r) for r in leads]
        if workers and workers > 1 and len(rows) > 1:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=workers) as ex:
                return list(ex.map(lambda ne: self.enrich_one(ne[0], ne[1]), rows))
        return [self.enrich_one(name, email) for name, email in rows]

    def enrich_dataframe(self, df, name_col: str = None, email_col: str = None):
        """Enrich a pandas DataFrame, returning a new DataFrame with added columns."""
        import pandas as pd
        cols = list(df.columns)
        name_col = name_col or cols[0]
        email_col = email_col or cols[1]
        leads = self.enrich(zip(df[name_col], df[email_col]))
        add = pd.DataFrame([l.as_dict() for l in leads],
                           columns=["title", "workplace", "link", "confidence",
                                    "is_role_account", "notes"])
        add.index = df.index
        return pd.concat([df, add], axis=1)


def _unpack(row: LeadInput):
    if isinstance(row, dict):
        name = row.get("name") or row.get("Name") or ""
        email = row.get("email") or row.get("mail") or row.get("Email") or ""
        return name, email
    seq = list(row)
    return (seq[0] if seq else ""), (seq[1] if len(seq) > 1 else "")
