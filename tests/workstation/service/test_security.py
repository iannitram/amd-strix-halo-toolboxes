"""Locked tests for #35 (workstation/service/security.py). One test per Expectation sentence."""

import pytest

from workstation.service.security import check_request, host_of

TOKEN = "t0k3n"
GOOD = {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765", "X-CSRF-Token": TOKEN}


def post(headers, method="POST", **kw):
    return check_request(method, headers, csrf_token=TOKEN, **kw)


def test_e1_host_of():
    assert host_of(" LocalHost:8765 ") == "localhost"
    assert host_of("[::1]:8765") == "::1"
    assert host_of("127.0.0.1") == "127.0.0.1"


def test_e2_headers_case_insensitive_and_not_mutated():
    headers = {"host": "localhost", "ORIGIN": "http://localhost:8765", "x-csrf-token": TOKEN}
    before = dict(headers)
    assert post(headers) is None
    assert headers == before


def test_e3_host_checks():
    assert post({"X-CSRF-Token": TOKEN}) == "missing host"
    assert post({"Host": "  "}) == "missing host"
    assert post({**GOOD, "Host": "evil.example:8765"}) == "bad host"
    assert check_request("GET", {"Host": "evil.example"}, csrf_token=TOKEN) == "bad host"
    assert post({**GOOD, "Host": "box.lan"}, allowed_hosts={"box.lan"}) == "bad origin"


def test_e4_safe_methods_pass_after_host():
    for m in ("GET", "HEAD", "OPTIONS", "get"):
        assert check_request(m, {"Host": "localhost", "Origin": "null"}, csrf_token=TOKEN) is None


def test_e5_bad_origin():
    assert post({**GOOD, "Origin": "null"}) == "bad origin"
    assert post({**GOOD, "Origin": "http://evil.example"}) == "bad origin"
    assert post({**GOOD, "Origin": "http://[::1]:8765"}) is None


def test_e6_cross_site():
    assert post({**GOOD, "Sec-Fetch-Site": "cross-site"}) == "cross-site request"
    assert post({**GOOD, "Sec-Fetch-Site": "same-origin"}) is None


def test_e7_csrf_token():
    assert post({**GOOD, "X-CSRF-Token": "wrong"}) == "bad csrf token"
    no_token = {k: v for k, v in GOOD.items() if k != "X-CSRF-Token"}
    assert post(no_token) == "bad csrf token"
    assert post(GOOD) is None


def test_e8_empty_server_token():
    with pytest.raises(ValueError, match="^csrf_token must not be empty$"):
        check_request("GET", GOOD, csrf_token="")
