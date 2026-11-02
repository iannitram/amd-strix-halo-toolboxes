"""Host, origin and CSRF checks for every request (M1). Planned: #35."""

import hmac
from urllib.parse import urlsplit

DEFAULT_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def host_of(value: str) -> str:
    value = value.strip()
    if value.startswith("["):
        closing = value.find("]")
        if closing != -1:
            return value[1:closing].lower()
    return value.split(":", 1)[0].lower()


def check_request(method, headers, *, csrf_token, allowed_hosts=DEFAULT_ALLOWED_HOSTS):
    """Return None when the request may proceed, else a short reason string."""
    if not csrf_token:
        raise ValueError("csrf_token must not be empty")

    normalized_headers = {name.lower(): value for name, value in headers.items()}
    host = normalized_headers.get("host")
    if host is None or not host.strip():
        return "missing host"
    allowed_hosts = {allowed.lower() for allowed in allowed_hosts}
    if host_of(host) not in allowed_hosts:
        return "bad host"

    if method.upper() in SAFE_METHODS:
        return None

    origin = normalized_headers.get("origin")
    if origin is not None:
        origin = origin.strip()
        if origin.lower() == "null":
            return "bad origin"
        try:
            origin_host = urlsplit(origin).hostname
        except ValueError:
            origin_host = None
        if origin_host is None or origin_host.lower() not in allowed_hosts:
            return "bad origin"

    if normalized_headers.get("sec-fetch-site", "").strip().lower() == "cross-site":
        return "cross-site request"

    token = normalized_headers.get("x-csrf-token")
    if token is None or not hmac.compare_digest(token.encode("utf-8"), csrf_token.encode("utf-8")):
        return "bad csrf token"
    return None
