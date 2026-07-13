from leadsearch import parse_linkedin


def test_dash_title_company():
    p = parse_linkedin("Jane Doe - Head of Data & AI - Acme | LinkedIn")
    assert p.name == "Jane Doe"
    assert p.title == "Head of Data & AI"
    assert p.company == "Acme"


def test_title_at_company():
    p = parse_linkedin("John Smith - Senior Engineer at Globex | LinkedIn")
    assert p.name == "John Smith"
    assert p.title == "Senior Engineer"
    assert p.company == "Globex"


def test_title_only_company_from_snippet():
    p = parse_linkedin("Jane Doe - Head of Data | LinkedIn",
                       snippet="Head of Data at Acme. Copenhagen, Denmark.")
    assert p.title == "Head of Data"
    assert p.company == "Acme"


def test_trailer_variants():
    p = parse_linkedin("Jane Doe – Product Lead – Initech – LinkedIn")
    assert p.title == "Product Lead"
    assert p.company == "Initech"
