import os

from leadsearch import (CachingProvider, JSONFileCache, LeadSearch, MemoryCache,
                        MockProvider, analyze_domain)
from leadsearch.types import SearchItem

ITEM = SearchItem(title="Jane Doe - Head of Data - Acme | LinkedIn",
                  link="https://linkedin.com/in/janedoe")


# ---- caching ----------------------------------------------------------------
def test_caching_provider_serves_repeats():
    base = MockProvider(items=[ITEM])
    cached = CachingProvider(base, MemoryCache())
    cached.search("q1")
    cached.search("q1")            # repeat -> cache hit, no second backend call
    cached.search("q2")
    assert base.calls == ["q1", "q2"]     # backend hit once per unique query
    assert cached.hits == 1 and cached.misses == 2


def test_json_file_cache_persists(tmp_path):
    path = os.path.join(tmp_path, "c.json")
    base = MockProvider(items=[ITEM])
    CachingProvider(base, JSONFileCache(path)).search("q")
    # a fresh cache reading the same file serves without calling the backend
    base2 = MockProvider(fn=lambda q, n: (_ for _ in ()).throw(AssertionError("should not call")))
    out = CachingProvider(base2, JSONFileCache(path)).search("q")
    assert out and out[0].link == ITEM.link


def test_caching_cuts_api_calls_across_leads():
    base = MockProvider(items=[ITEM])
    ls = LeadSearch(CachingProvider(base))
    # same person twice -> identical queries -> backend seen once per unique query
    ls.enrich([("Jane Doe", "jane@acme.com"), ("Jane Doe", "jane@acme.com")])
    assert len(set(base.calls)) == len(base.calls) or base.calls.count(base.calls[0]) == 1


# ---- MX / domain intelligence ----------------------------------------------
def test_workspace_domain_is_corporate():
    mx = {"acme.com": ["aspmx.l.google.com"], "nope.com": []}
    info = analyze_domain("acme.com", lambda d: mx.get(d, []))
    assert info.deliverable and info.provider == "google"
    assert info.is_corporate and info.company_guess == "Acme"

    dead = analyze_domain("nope.com", lambda d: mx.get(d, []))
    assert not dead.deliverable and not dead.is_corporate


def test_mx_lookup_upgrades_and_notes():
    provider = MockProvider(items=[ITEM])
    mx = {"acme.com": ["outlook-com.olc.protection.outlook.com"]}
    ls = LeadSearch(provider, mx_lookup=lambda d: mx.get(d, []))
    lead = ls.enrich_one("Jane Doe", "jane@acme.com")
    assert any("microsoft" in n for n in lead.notes)

    ls2 = LeadSearch(MockProvider(items=[]), mx_lookup=lambda d: [])
    dead = ls2.enrich_one("Bob", "bob@ghost.example")
    assert any("no MX" in n for n in dead.notes)


# ---- concurrent bulk --------------------------------------------------------
def test_bulk_workers_preserve_order_and_results():
    provider = MockProvider(items=[ITEM])
    ls = LeadSearch(provider)
    leads = [("Jane Doe", f"jane{i}@acme.com") for i in range(20)]
    serial = ls.enrich(leads, workers=1)
    parallel = ls.enrich(leads, workers=8)
    assert [l.email for l in parallel] == [l.email for l in serial]   # order kept
    assert all(l.title == "Head of Data" for l in parallel)
