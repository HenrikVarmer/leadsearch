# leadsearch

> Turn a list of names & e-mails into **job titles, workplaces and LinkedIn
> profiles** — with e-mail intelligence and result scoring, not just "the first
> hit".

<p>
<a href="https://github.com/HenrikVarmer/leadsearch/actions/workflows/tests.yaml"><img src="https://github.com/HenrikVarmer/leadsearch/actions/workflows/tests.yaml/badge.svg" alt="tests"></a>
<img src="https://img.shields.io/badge/python-%E2%89%A5%203.9-3776AB?logo=python&logoColor=white" alt="Python ≥ 3.9">
<img src="https://img.shields.io/badge/license-MIT-green" alt="MIT">
</p>

`leadsearch` enriches a table of leads by querying a search engine
(Google Programmable Search or Bing) restricted to LinkedIn, then parsing and
**scoring** the results to pick the best match for each lead.

### Smarter than a first-result grab

- **E-mail intelligence** — infers the **company** from the domain
  (`jane@acme-corp.co.uk` → *Acme Corp*), guesses a **name** from the local part
  when none is given (`jane.doe@…` → *Jane Doe*), and flags **free**, **role**
  (`info@`, `sales@`) and **disposable** accounts so they don't pollute results.
- **Candidate scoring** — every result in the top-N is scored on fuzzy **name
  similarity**, whether the URL is a real personal profile, and whether the
  result's company agrees with the e-mail's domain. The best-scoring candidate
  wins, with a **confidence** value — not just `items[0]`.
- **Robust parsing** — handles the common LinkedIn title shapes
  (`Name - Title - Company`, `Name - Title at Company`, snippet-only company).
- **Pluggable providers** — Google, Bing, or a `MockProvider` so the whole
  pipeline is testable offline. Retries with backoff + a politeness delay.

## Install

```bash
pip install -e ".[test]"          # add ".[pandas]" for DataFrame support
```

## Usage

```python
from leadsearch import LeadSearch, GoogleProvider

ls = LeadSearch(GoogleProvider(api_key="YOUR_KEY", cx="YOUR_CX"))

leads = ls.enrich([
    ("Jane Doe", "jane.doe@acme.com"),
    ("", "john.smith@globex.io"),      # name recovered from the address
    ("Sales", "sales@acme.com"),       # flagged as a role account
])

for lead in leads:
    print(lead.as_dict())
# {'name': 'Jane Doe', 'title': 'Head of Data', 'workplace': 'Acme',
#  'link': 'https://linkedin.com/in/janedoe', 'confidence': 0.86, ...}
```

Bing works the same way via `BingProvider(api_key="…")`. A pandas frame:

```python
enriched = ls.enrich_dataframe(df, name_col="name", email_col="email")
```

### Testing offline

```python
from leadsearch import LeadSearch, MockProvider
from leadsearch.types import SearchItem

mock = MockProvider(items=[SearchItem(title="Jane Doe - Head of Data - Acme | LinkedIn",
                                      link="https://linkedin.com/in/janedoe")])
LeadSearch(mock).enrich_one("Jane Doe", "jane@acme.com")
```

## API

| Object | Purpose |
|--------|---------|
| `LeadSearch(provider)` | `.enrich(leads)`, `.enrich_one(name, email)`, `.enrich_dataframe(df)` |
| `GoogleProvider` / `BingProvider` / `MockProvider` | Search backends |
| `analyze_email(email)` | Company / name / account-type inference |
| `parse_linkedin(title, snippet)` | Parse a result into name/title/company |
| `score_candidate` / `rank_candidates` | Result scoring |
| `Lead` | Enriched result dataclass |

## Getting API keys

Google [Programmable Search](https://developers.google.com/custom-search/v1/overview)
(an API key + a search-engine `cx`) or the Bing Web Search API.

## R version

The original R implementation lives at
**[HenrikVarmer/LeadSearch-R](https://github.com/HenrikVarmer/LeadSearch-R)**.

## License

MIT © Henrik Varmer
