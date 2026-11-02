"""Host, origin and CSRF checks for every request (M1). Planned: #35."""

DEFAULT_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def host_of(value: str) -> str:
    raise NotImplementedError("TODO #35")


def check_request(method, headers, *, csrf_token, allowed_hosts=DEFAULT_ALLOWED_HOSTS):
    """Return None when the request may proceed, else a short reason string."""
    raise NotImplementedError("TODO #35")
