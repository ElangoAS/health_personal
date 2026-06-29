from app.google_auth import is_email_allowed, normalize_email


def test_normalize_email_lowercases_and_trims():
    assert normalize_email("  User@Example.COM  ") == "user@example.com"


def test_is_email_allowed_matches_allowlist_case_insensitively():
    allowed = ["Admin@Example.com", "runner@test.org"]
    assert is_email_allowed("admin@example.com", allowed)
    assert is_email_allowed("runner@test.org", allowed)
    assert not is_email_allowed("stranger@example.com", allowed)


def test_is_email_allowed_rejects_empty_email():
    assert not is_email_allowed(None, ["user@example.com"])
    assert not is_email_allowed("", ["user@example.com"])


def test_is_email_allowed_rejects_when_allowlist_empty():
    assert not is_email_allowed("user@example.com", [])
