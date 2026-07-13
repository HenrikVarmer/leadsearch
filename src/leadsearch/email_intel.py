"""E-mail intelligence: infer company, person and account type from an address.

This is where ``leadsearch`` is smarter than the original: instead of a simple
free-mail check, an address is decomposed into everything it can tell us — the
likely company, a name guess, and whether it's a personal, role, free or
disposable account — so the search query can be built with the strongest
available signal.
"""

from __future__ import annotations

import re

from .types import EmailInfo

__all__ = ["analyze_email", "company_from_domain", "name_from_local", "FREE_MAIL_DOMAINS"]

# Free / ISP webmail — the domain carries no company signal.
FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "hotmail.com", "hotmail.co.uk", "outlook.com",
    "live.com", "msn.com", "yahoo.com", "yahoo.co.uk", "ymail.com", "icloud.com",
    "me.com", "mac.com", "aol.com", "gmx.com", "gmx.de", "mail.com", "proton.me",
    "protonmail.com", "zoho.com", "yandex.com", "web.de", "t-online.de",
    # regional / ISP
    "jubii.dk", "stofanet.dk", "post.dk", "mail.dk", "hotmail.dk", "live.dk",
}

# Obvious disposable / throwaway providers.
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "trashmail.com", "yopmail.com", "getnada.com", "sharklasers.com",
}

# Local-parts that indicate a shared / role inbox rather than a person.
ROLE_LOCALPARTS = {
    "info", "sales", "support", "admin", "administrator", "contact", "hello",
    "hi", "office", "hr", "jobs", "careers", "recruiting", "marketing", "press",
    "media", "billing", "accounts", "accounting", "finance", "legal", "noreply",
    "no-reply", "donotreply", "webmaster", "postmaster", "help", "service",
    "services", "team", "mail", "enquiries", "inquiries", "general",
}

# Multi-part public suffixes we must strip to reach the registrable name.
_COMPOUND_TLDS = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "co.nz", "co.za", "com.au", "net.au",
    "com.br", "co.jp", "co.in", "com.mx",
}

_GENERIC_TOKENS = {"mail", "email", "smtp", "corp", "group", "holding", "inc", "llc"}


def company_from_domain(domain: str) -> str | None:
    """Infer a human-readable company name from a domain.

    ``acme.com`` -> ``"Acme"``; ``sub.acme-corp.co.uk`` -> ``"Acme Corp"``.
    Returns ``None`` for free / disposable domains.
    """
    domain = (domain or "").strip().lower().lstrip("@")
    if not domain or domain in FREE_MAIL_DOMAINS or domain in DISPOSABLE_DOMAINS:
        return None
    if domain.startswith("www."):
        domain = domain[4:]
    parts = domain.split(".")
    # strip a compound public suffix, else the last label (tld)
    if len(parts) >= 3 and ".".join(parts[-2:]) in _COMPOUND_TLDS:
        core = parts[-3]
    elif len(parts) >= 2:
        core = parts[-2]
    else:
        core = parts[0]
    if core in _GENERIC_TOKENS or not core:
        return None
    words = [w for w in re.split(r"[-_]+", core) if w]
    return " ".join(w.capitalize() for w in words) or None


def name_from_local(local: str) -> str | None:
    """Guess a person's name from the local part of an address.

    ``jane.doe`` -> ``"Jane Doe"``; ``jdoe`` / ``sales`` -> ``None``.
    """
    local = re.sub(r"\+.*$", "", (local or "").lower())  # drop +tag
    local = re.sub(r"\d+", "", local)
    tokens = [t for t in re.split(r"[._\-]+", local) if len(t) >= 2]
    if len(tokens) >= 2:
        return " ".join(t.capitalize() for t in tokens[:3])
    return None


def analyze_email(email: str) -> EmailInfo:
    """Decompose an address into everything it can tell us."""
    email = (email or "").strip()
    local, _, domain = email.partition("@")
    local, domain = local.lower(), domain.lower()
    info = EmailInfo(email=email, local=local, domain=domain)
    info.is_free = domain in FREE_MAIL_DOMAINS
    info.is_disposable = domain in DISPOSABLE_DOMAINS
    info.is_role = local in ROLE_LOCALPARTS
    if not info.is_free and not info.is_disposable:
        info.company_guess = company_from_domain(domain)
    if not info.is_role:
        info.name_guess = name_from_local(local)
    return info
