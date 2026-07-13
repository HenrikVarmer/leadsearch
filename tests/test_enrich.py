from leadsearch import LeadSearch, MockProvider
from leadsearch.types import SearchItem


def test_enrich_picks_best_and_sets_confidence():
    provider = MockProvider(items=[
        SearchItem(title="Someone Else - Analyst - Other | LinkedIn",
                   link="https://linkedin.com/in/else"),
        SearchItem(title="Jane Doe - Head of Data - Acme | LinkedIn",
                   link="https://linkedin.com/in/janedoe",
                   snippet="Head of Data at Acme."),
    ])
    ls = LeadSearch(provider)
    lead = ls.enrich_one("Jane Doe", "jane.doe@acme.com")
    assert lead.title == "Head of Data"
    assert lead.workplace == "Acme"
    assert "janedoe" in lead.link
    assert lead.confidence >= 0.35


def test_free_mail_skips_company_in_query():
    provider = MockProvider(items=[
        SearchItem(title="John Smith - Engineer - Globex | LinkedIn",
                   link="https://linkedin.com/in/johnsmith"),
    ])
    ls = LeadSearch(provider)
    ls.enrich_one("John Smith", "john@gmail.com")
    # only the name-only query should have been issued (no company appended)
    assert all("gmail" not in q.lower() for q in provider.calls)
    assert all("globex" not in q.lower() for q in provider.calls)


def test_role_account_flagged():
    ls = LeadSearch(MockProvider(items=[]))
    lead = ls.enrich_one("", "info@acme.com")
    assert lead.is_role_account
    assert lead.title == "No Result"


def test_name_recovered_from_email_when_missing():
    provider = MockProvider(items=[
        SearchItem(title="Jane Doe - Head of Data - Acme | LinkedIn",
                   link="https://linkedin.com/in/janedoe"),
    ])
    lead = LeadSearch(provider).enrich_one("", "jane.doe@acme.com")
    assert lead.name == "Jane Doe"


def test_weak_match_discarded():
    provider = MockProvider(items=[
        SearchItem(title="Totally Different - CEO - Nope | LinkedIn",
                   link="https://example.com/x"),
    ])
    lead = LeadSearch(provider, min_confidence=0.5).enrich_one("Jane Doe", "jane@acme.com")
    assert lead.title == "No Result"
    assert lead.confidence == 0.0


def test_batch_and_dict_input():
    provider = MockProvider(items=[
        SearchItem(title="Jane Doe - Head of Data - Acme | LinkedIn",
                   link="https://linkedin.com/in/janedoe"),
    ])
    ls = LeadSearch(provider)
    out = ls.enrich([("Jane Doe", "jane@acme.com"), {"name": "Jane Doe", "email": "jane@acme.com"}])
    assert len(out) == 2 and all(l.email for l in out)
