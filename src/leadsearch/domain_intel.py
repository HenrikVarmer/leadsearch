"""Domain intelligence via MX records.

A custom domain hosted on Google Workspace or Microsoft 365 is **not** free
webmail — it's a company, and the company name carries signal. Looking at a
domain's MX records tells us who hosts its mail and confirms the domain can even
receive mail. The MX lookup is injectable so the logic is fully testable and the
DNS dependency (``dnspython``) stays optional.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .email_intel import FREE_MAIL_DOMAINS, company_from_domain

__all__ = ["DomainInfo", "analyze_domain", "default_mx_lookup"]

# MX host substring -> mail-hosting provider label
_MX_PROVIDERS = {
    "google.com": "google", "googlemail.com": "google", "aspmx.l.google.com": "google",
    "outlook.com": "microsoft", "microsoft.com": "microsoft", "protection.outlook.com": "microsoft",
    "pphosted.com": "proofpoint", "mimecast.com": "mimecast",
    "zoho.com": "zoho", "amazonaws.com": "amazon-ses", "messagingengine.com": "fastmail",
}


@dataclass
class DomainInfo:
    domain: str
    deliverable: bool = False        # has at least one MX record
    mail_host: Optional[str] = None  # first MX host
    provider: Optional[str] = None   # google / microsoft / ...
    is_free: bool = False
    is_corporate: bool = False       # custom domain that can receive mail
    company_guess: Optional[str] = None


def default_mx_lookup(domain: str) -> list[str]:
    """Resolve MX hosts for ``domain`` using ``dnspython`` if available.

    Returns an empty list when DNS can't be resolved or ``dnspython`` isn't
    installed — callers degrade gracefully.
    """
    try:
        import dns.resolver  # type: ignore
    except Exception:
        return []
    try:
        answers = dns.resolver.resolve(domain, "MX")
        return [str(r.exchange).rstrip(".").lower() for r in answers]
    except Exception:
        return []


def analyze_domain(domain: str, mx_lookup: Optional[Callable[[str], list]] = None) -> DomainInfo:
    """Classify a domain using its MX records.

    ``mx_lookup`` is a ``domain -> [mx_host, ...]`` callable (injected in tests;
    defaults to a best-effort DNS lookup).
    """
    domain = (domain or "").strip().lower().lstrip("@")
    info = DomainInfo(domain=domain)
    info.is_free = domain in FREE_MAIL_DOMAINS
    info.company_guess = company_from_domain(domain)

    hosts = (mx_lookup or default_mx_lookup)(domain) or []
    if hosts:
        info.deliverable = True
        info.mail_host = hosts[0]
        for needle, label in _MX_PROVIDERS.items():
            if any(needle in h for h in hosts):
                info.provider = label
                break
    # a deliverable, non-free domain is a real company mailbox
    info.is_corporate = info.deliverable and not info.is_free
    return info
