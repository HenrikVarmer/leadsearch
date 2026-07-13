from leadsearch import analyze_email, company_from_domain, name_from_local


def test_company_from_domain():
    assert company_from_domain("acme.com") == "Acme"
    assert company_from_domain("acme-corp.io") == "Acme Corp"
    assert company_from_domain("mail.acme.co.uk") == "Acme"
    assert company_from_domain("gmail.com") is None          # free
    assert company_from_domain("mailinator.com") is None     # disposable


def test_name_from_local():
    assert name_from_local("jane.doe") == "Jane Doe"
    assert name_from_local("john_smith99") == "John Smith"
    assert name_from_local("jane.van.doe") == "Jane Van Doe"
    assert name_from_local("jdoe") is None                   # single token
    assert name_from_local("sales") is None


def test_analyze_free_and_company():
    free = analyze_email("john@gmail.com")
    assert free.is_free and free.company_guess is None and free.name_guess is None

    corp = analyze_email("jane.doe@acme.com")
    assert not corp.is_free
    assert corp.company_guess == "Acme"
    assert corp.name_guess == "Jane Doe"


def test_role_and_disposable():
    role = analyze_email("info@acme.com")
    assert role.is_role and role.name_guess is None
    dis = analyze_email("x@mailinator.com")
    assert dis.is_disposable
