import re
from urllib.parse import urlsplit

DOMAIN_PATTERN = re.compile(
    r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


def normalize_domain(value) -> str:
    # Return the canonical form of a domain: lowercase host, no scheme, path, port or www.
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Invalid domain: {value!r}")
    value = value.strip().lower()
    host = urlsplit(value if "://" in value else f"//{value}").hostname or ""
    host = host.removeprefix("www.")
    if not DOMAIN_PATTERN.fullmatch(host):
        raise ValueError(f"Invalid domain: {value!r}")
    return host
