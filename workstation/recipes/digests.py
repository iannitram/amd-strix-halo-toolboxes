"""Resolve mutable image tags to immutable OCI manifest digests (R1)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request

from workstation.errors import WorkstationError

_DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)


def _http_fetch(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()


def _repository_parts(repository: str) -> tuple[str, str]:
    if not isinstance(repository, str) or not repository or "@" in repository:
        raise WorkstationError("invalid image repository")
    pieces = repository.split("/", 1)
    if len(pieces) == 1:
        host, path = "docker.io", f"library/{pieces[0]}"
    elif "." in pieces[0] or ":" in pieces[0] or pieces[0] == "localhost":
        host, path = pieces
    else:
        host, path = "docker.io", repository
    if host == "index.docker.io":
        host = "docker.io"
    if host == "docker.io" and "/" not in path:
        path = f"library/{path}"
    if not path or any(part in ("", ".", "..") for part in path.split("/")):
        raise WorkstationError("invalid image repository")
    return host, path


def _call_fetch(fetch, url: str, headers: dict[str, str]):
    try:
        result = fetch(url, headers)
    except Exception as error:
        raise WorkstationError("could not contact image registry") from error
    if isinstance(result, tuple) and len(result) == 3:
        return result
    if isinstance(result, dict):
        return result.get("status", 200), result.get("headers", {}), result.get("body", b"")
    raise WorkstationError("invalid response from image registry")


def _header(headers, name: str) -> str | None:
    return next((value for key, value in headers.items() if key.lower() == name.lower()), None)


def resolve_digest(repository: str, tag: str, *, fetch=None) -> str:
    """Return the registry's ``sha256:<64 hex>`` digest for ``repository:tag``.

    ``fetch`` is called as ``fetch(url, headers)`` and returns ``(status, headers,
    body)`` (or a mapping with those keys). The default implementation uses urllib.
    """
    if not isinstance(tag, str) or not tag or "/" in tag or "@" in tag:
        raise WorkstationError("invalid image tag")
    host, path = _repository_parts(repository)
    fetch = fetch or _http_fetch
    registry_host = "registry-1.docker.io" if host == "docker.io" else host
    manifest_url = (
        f"https://{registry_host}/v2/{path}/manifests/"
        f"{urllib.parse.quote(tag, safe='._-')}"
    )
    headers = {"Accept": _ACCEPT}

    status, response_headers, body = _call_fetch(fetch, manifest_url, headers)
    if status == 401:
        challenge = _header(response_headers, "WWW-Authenticate") or ""
        match = re.fullmatch(r"Bearer\s+(.+)", challenge, flags=re.IGNORECASE)
        if not match or host not in ("docker.io", "quay.io"):
            raise WorkstationError("image registry authorization failed")
        params = dict(re.findall(r'(\w+)="([^\"]*)"', match.group(1)))
        realm = params.get("realm")
        if not realm or urllib.parse.urlparse(realm).scheme != "https":
            raise WorkstationError("image registry returned an invalid auth challenge")
        query = {key: value for key, value in params.items() if key in ("service",)}
        query["scope"] = f"repository:{path}:pull"
        token_url = f"{realm}?{urllib.parse.urlencode(query)}"
        token_status, _, token_body = _call_fetch(fetch, token_url, {})
        if token_status != 200:
            raise WorkstationError("image registry authorization failed")
        try:
            token_data = json.loads(token_body)
            token = token_data.get("token") or token_data.get("access_token")
        except (TypeError, ValueError, AttributeError):
            token = None
        if not isinstance(token, str) or not token:
            raise WorkstationError("image registry returned an invalid token")
        headers["Authorization"] = f"Bearer {token}"
        status, response_headers, body = _call_fetch(fetch, manifest_url, headers)

    if status == 404:
        raise WorkstationError("image tag was not found")
    if status != 200:
        raise WorkstationError("image registry request failed")
    digest = _header(response_headers, "Docker-Content-Digest")
    if not digest and body:
        raise WorkstationError("image registry omitted the manifest digest")
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise WorkstationError("image registry returned an invalid manifest digest")
    return digest.lower()
