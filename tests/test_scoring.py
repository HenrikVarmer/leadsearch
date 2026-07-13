from leadsearch import name_similarity, parse_linkedin, rank_candidates
from leadsearch.types import SearchItem


def test_name_similarity():
    assert name_similarity("Jane Doe", "Jane Doe") == 1.0
    assert name_similarity("Jane Doe", "Doe, Jane") > 0.8      # token order
    assert name_similarity("Jane Doe", "Bob Smith") < 0.3


def test_ranking_prefers_matching_name_and_profile_url():
    items = [
        SearchItem(title="Bob Smith - CTO - Globex | LinkedIn",
                   link="https://linkedin.com/in/bobsmith"),
        SearchItem(title="Jane Doe - Head of Data - Acme | LinkedIn",
                   link="https://linkedin.com/in/janedoe"),
        SearchItem(title="Acme | LinkedIn",
                   link="https://linkedin.com/company/acme"),
    ]
    ranked = rank_candidates(items, "Jane Doe", "Acme", parse_linkedin)
    assert ranked[0].parsed.name == "Jane Doe"
    assert ranked[0].score > ranked[1].score
    # the company page (no personal profile url) ranks last
    assert "company/acme" in ranked[-1].item.link
