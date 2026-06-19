from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_url(url: str) -> str:
    """Return a stable URL representation suitable for registry identity."""
    value = (url or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value

    parts = urlsplit(value)
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()

    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parts.path or "/"
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((scheme, netloc, path, query, ""))


def canonical_domain(url: str) -> str:
    normalized = normalize_url(url)
    if not normalized:
        return ""
    return urlsplit(normalized).netloc.lower()


def make_source_id(country_code: str, official_url: str, name: str = "") -> str:
    base = "|".join(
        [
            (country_code or "").strip().upper(),
            normalize_url(official_url),
            (name or "").strip(),
        ]
    )
    return "src_" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]
