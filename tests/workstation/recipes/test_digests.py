"""Registry digest resolution tests use only an injected fetch function."""

import json

import pytest

from workstation.errors import WorkstationError
from workstation.recipes.digests import resolve_digest

DIGEST = "sha256:" + "a" * 64


def test_resolves_public_registry_manifest_without_auth():
    calls = []

    def fetch(url, headers):
        calls.append((url, headers))
        return 200, {"Docker-Content-Digest": DIGEST}, b"manifest"

    assert resolve_digest("ghcr.io/example/model", "v1", fetch=fetch) == DIGEST
    assert calls[0][0] == "https://ghcr.io/v2/example/model/manifests/v1"
    assert "application/vnd.oci.image.manifest.v1+json" in calls[0][1]["Accept"]


@pytest.mark.parametrize("host", ["docker.io", "quay.io"])
def test_uses_anonymous_bearer_token_flow(host):
    calls = []

    def fetch(url, headers):
        calls.append((url, headers))
        if len(calls) == 1:
            return 401, {
                "WWW-Authenticate": (
                    f'Bearer realm="https://{host}/token",service="{host}",'
                    'scope="repository:someone/model:pull"'
                )
            }, b""
        if "/token?" in url:
            return 200, {}, json.dumps({"token": "anonymous-token"}).encode()
        return 200, {"Docker-Content-Digest": DIGEST}, b"manifest"

    assert resolve_digest(f"{host}/someone/model", "stable", fetch=fetch) == DIGEST
    assert len(calls) == 3
    assert "scope=repository%3Asomeone%2Fmodel%3Apull" in calls[1][0]
    assert calls[2][1]["Authorization"] == "Bearer anonymous-token"


def test_normalizes_short_docker_hub_repository():
    def fetch(url, headers):
        assert url == "https://registry-1.docker.io/v2/library/llama/manifests/latest"
        return 200, {"docker-content-digest": DIGEST}, b""

    assert resolve_digest("llama", "latest", fetch=fetch) == DIGEST


@pytest.mark.parametrize(
    ("status", "headers", "message"),
    [
        (404, {}, "not found"),
        (500, {}, "request failed"),
        (200, {}, "invalid manifest digest"),
        (200, {"Docker-Content-Digest": "sha256:bad"}, "invalid manifest digest"),
    ],
)
def test_rejects_registry_failures_and_missing_digest(status, headers, message):
    with pytest.raises(WorkstationError, match=message):
        resolve_digest("docker.io/example/model", "latest", fetch=lambda *_: (status, headers, b""))


def test_transport_failure_is_a_plain_workstation_error():
    def fail(*_):
        raise OSError("private transport detail")

    with pytest.raises(WorkstationError, match="could not contact image registry") as error:
        resolve_digest("example.com/model", "v1", fetch=fail)
    assert "private transport detail" not in str(error.value)


def test_rejects_malformed_auth_challenge():
    def fetch(*_):
        return 401, {"WWW-Authenticate": 'Bearer realm="http://unsafe/token"'}, b""

    with pytest.raises(WorkstationError, match="invalid auth challenge"):
        resolve_digest("quay.io/example/model", "latest", fetch=fetch)
