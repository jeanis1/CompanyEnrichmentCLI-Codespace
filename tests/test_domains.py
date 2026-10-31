import pytest

from services.domains import normalize_domain


@pytest.mark.parametrize(
    "raw",
    [
        "https://www.Stripe.com/pricing",
        " STRIPE.COM ",
        "stripe.com:443",
    ],
)
def test_normalizes_to_canonical_domain(raw):
    assert normalize_domain(raw) == "stripe.com"


@pytest.mark.parametrize("raw", ["", None, "not a domain"])
def test_invaid_domains_raise(raw):
    with pytest.raises(ValueError):
        normalize_domain(raw)
