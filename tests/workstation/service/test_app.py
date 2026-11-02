"""Loopback HTTP integration tests; no containers, external connections or GPU."""

import json
import re
import subprocess
import sys
import time
from contextlib import closing, contextmanager
from http.client import HTTPConnection
from queue import Queue
from threading import Event, Thread

import pytest

from workstation.__main__ import main
from workstation.runtime.fake import FakeRuntime
from workstation.service import app


@contextmanager
def running(**kwargs):
    kwargs.setdefault("runtime", FakeRuntime(devices={"fake": True}))
    server = app.create_server(port=0, **kwargs)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()


@pytest.fixture
def service():
    with running() as server:
        yield server


def connection(service):
    return closing(HTTPConnection("127.0.0.1", service.server_port, timeout=3))


def request(service, method, path, *, headers=None, body=None):
    with connection(service) as conn:
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()


def token(service):
    status, headers, page = request(service, "GET", "/")
    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    return re.search(rb'<meta name="csrf-token" content="([^"]+)">', page)[1].decode()


def post(service, path="/api/operations", *, body=None, csrf=None):
    return request(service, "POST", path, body=body,
                   headers={"X-CSRF-Token": csrf or token(service),
                            "Content-Type": "application/json"})


def wait_state(service, op_id, state):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        status, _, body = request(service, "GET", f"/api/operations/{op_id}")
        assert status == 200
        operation = json.loads(body)
        if operation["state"] == state:
            return operation
        time.sleep(0.01)
    pytest.fail(f"operation did not reach {state}")


def read_event(response):
    frame = {}
    while True:
        raw = response.readline()
        assert raw, "event stream closed before the next event"
        line = raw.decode().rstrip("\r\n")
        if not line:
            if "data" in frame:
                return int(frame["id"]), json.loads(frame["data"])
        elif not line.startswith(":"):
            name, value = line.split(": ", 1)
            frame[name] = value


def test_default_bind_and_page_bootstrap(service):
    assert service.server_address[0] == "127.0.0.1"
    assert service.server_port > 0
    assert isinstance(service.runtime, FakeRuntime)
    assert token(service) == token(service)
    with running() as other:
        assert token(other) != token(service)
    status, headers, body = request(service, "HEAD", "/")
    assert status == 200 and body == b""
    assert int(headers["Content-Length"]) > 0
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]


@pytest.mark.parametrize("host", ["0.0.0.0", "::1", "localhost", "192.0.2.1"])
def test_other_bind_addresses_require_explicit_flag(host):
    with pytest.raises(ValueError, match="allow_lan"):
        app.serve(host=host, port=0, runtime=FakeRuntime())


def test_explicit_lan_bind_still_checks_hosts():
    with running(host="0.0.0.0", allow_lan=True) as service:
        assert service.server_address[0] == "0.0.0.0"
        assert request(service, "GET", "/", headers={"Host": "untrusted.invalid"})[0] == 403
        assert request(service, "GET", "/")[0] == 200
    with running(host="0.0.0.0", allow_lan=True,
                 allowed_hosts={"192.0.2.1"}) as service:
        headers = {"Host": "192.0.2.1", "Origin": "http://192.0.2.1",
                   "X-CSRF-Token": service.csrf_token, "Content-Type": "application/json"}
        assert request(service, "POST", "/api/operations", headers=headers,
                       body='{"kind":"devices"}')[0] == 202
        assert request(service, "GET", "/")[0] == 403


@pytest.mark.parametrize("method,path", [
    ("GET", "/"), ("HEAD", "/styles.css"), ("GET", "/app.js"),
    ("GET", "/api/operations/events"), ("GET", "/api/operations/op-000001"),
    ("POST", "/api/operations"), ("POST", "/api/operations/op-000001/cancel"),
    ("OPTIONS", "/"), ("DELETE", "/"), ("PATCH", "/unknown"),
])
def test_every_route_and_method_passes_check_before_dispatch(service, monkeypatch, method, path):
    calls = []

    def refuse(method, headers, **kwargs):
        calls.append((method, kwargs))
        return "refused for test"

    monkeypatch.setattr(app, "check_request", refuse)
    status, _, body = request(service, method, path, body="not JSON")
    assert status == 403
    if method != "HEAD":
        assert json.loads(body) == {"error": "refused for test"}
    assert calls == [(method, {"csrf_token": service.csrf_token,
                               "allowed_hosts": service.allowed_hosts})]
    assert service.operations.events_since() == []
    assert service.runtime.images == set() and service.runtime.servers == {}


@pytest.mark.parametrize("headers,reason", [
    ({"Host": "untrusted.invalid"}, "bad host"),
    ({"Host": ""}, "missing host"),
    ({"Origin": "http://untrusted.invalid"}, "bad origin"),
    ({"Sec-Fetch-Site": "cross-site"}, "cross-site request"),
    ({"X-CSRF-Token": "wrong"}, "bad csrf token"),
])
def test_refusals_return_reason_without_starting_job(service, headers, reason):
    headers = {"X-CSRF-Token": token(service), "Content-Type": "application/json", **headers}
    status, _, body = request(service, "POST", "/api/operations",
                              headers=headers, body='{"kind":"devices"}')
    assert status == 403 and json.loads(body) == {"error": reason}
    assert service.operations.events_since() == []


def test_missing_token_cannot_submit_or_cancel(service):
    op_id = service.operations.create("devices")
    for path in ("/api/operations", f"/api/operations/{op_id}/cancel"):
        status, _, body = request(service, "POST", path, body='{"kind":"devices"}')
        assert status == 403 and json.loads(body)["error"] == "bad csrf token"
    assert service.operations.get(op_id)["state"] == "queued"


def test_duplicate_security_headers_and_missing_host_are_refused(service):
    with connection(service) as conn:
        conn.putrequest("GET", "/", skip_host=True)
        conn.endheaders()
        response = conn.getresponse()
        assert response.status == 403
        assert json.loads(response.read())["error"] == "missing host"
    with connection(service) as conn:
        conn.putrequest("POST", "/api/operations")
        conn.putheader("Host", "localhost")
        conn.putheader("X-CSRF-Token", token(service))
        conn.endheaders()
        response = conn.getresponse()
        assert response.status == 403
        assert json.loads(response.read())["error"] == "duplicate security header"
    assert service.operations.events_since() == []


def test_expect_continue_is_checked_before_accepting_body(service):
    with connection(service) as conn:
        conn.putrequest("POST", "/api/operations")
        conn.putheader("Expect", "100-continue")
        conn.putheader("Content-Length", "100")
        conn.endheaders()
        with conn.sock.makefile("rb") as stream:
            assert stream.readline().startswith(b"HTTP/1.1 403 ")
    assert service.operations.events_since() == []


@pytest.mark.parametrize("headers", [
    [("Content-Length", "-1")], [("Content-Length", "65537")],
    [("Content-Length", "bad")], [("Content-Length", "1"), ("Content-Length", "2")],
    [("Content-Length", "1"), ("Transfer-Encoding", "chunked")],
    [("Content-Length", "1"), ("Content-Type", "text/plain")], [],
])
def test_invalid_body_framing_is_rejected_before_read(service, headers):
    with connection(service) as conn:
        conn.putrequest("POST", "/api/operations")
        conn.putheader("X-CSRF-Token", token(service))
        for name, value in headers:
            conn.putheader(name, value)
        conn.endheaders()
        response = conn.getresponse()
        assert response.status == 400
        response.read()
    assert service.operations.events_since() == []


@pytest.mark.parametrize("path,mime", [("/styles.css", "text/css"),
                                       ("/app.js", "text/javascript")])
def test_page_assets(service, path, mime):
    status, headers, body = request(service, "GET", path)
    assert status == 200 and mime in headers["Content-Type"] and body


@pytest.mark.parametrize("path", ["/../service/app.py", "/%2e%2e/service/app.py",
                                 "/api/operations/unknown", "/unknown"])
def test_only_explicit_assets_and_routes_are_served(service, path):
    assert request(service, "GET", path)[0] == 404


def test_slow_runtime_returns_id_before_finishing():
    entered, release = Event(), Event()

    class SlowFake(FakeRuntime):
        def devices(self):
            entered.set()
            assert release.wait(3)
            return super().devices()

    try:
        with running(runtime=SlowFake(devices={"fake": True})) as service:
            status, _, body = post(service, body='{"kind":"devices"}')
            assert status == 202
            op_id = json.loads(body)["id"]
            assert entered.wait(3) and not release.is_set()
            assert service.operations.get(op_id)["state"] == "running"
            assert request(service, "GET", "/")[0] == 200
            release.set()
            assert wait_state(service, op_id, "succeeded")["detail"] == {"fake": True}
    finally:
        release.set()


def test_events_progress_cancellation_and_reconnect():
    entered, stopped = Event(), Event()

    def job(context):
        context.progress(0.25, message="checking")
        entered.set()
        try:
            while not context.operations.cancel_requested(context.op_id):
                time.sleep(0.01)
            context.check_cancelled()
            pytest.fail("cancellation did not stop the job")
        finally:
            stopped.set()

    with running(jobs={"check": job}) as service:
        csrf = token(service)
        status, _, body = post(service, body='{"kind":"check"}', csrf=csrf)
        assert status == 202
        op_id = json.loads(body)["id"]
        assert entered.wait(3)
        with connection(service) as conn:
            conn.request("GET", "/api/operations/events")
            stream = conn.getresponse()
            assert stream.status == 200
            assert stream.getheader("Content-Type") == "text/event-stream"
            events = [read_event(stream)[1] for _ in range(3)]
            assert [(e["seq"], e["state"], e["progress"]) for e in events] == [
                (1, "queued", 0.0), (2, "running", 0.0), (3, "running", 0.25)]
            assert events[-1]["message"] == "checking"
            status, _, _ = post(service, f"/api/operations/{op_id}/cancel", csrf=csrf)
            assert status == 200
            assert stopped.wait(3)
            assert read_event(stream)[1]["state"] == "cancelling"
            last_seq, event = read_event(stream)
            assert event["state"] == "cancelled" and event["op_id"] == op_id
        assert wait_state(service, op_id, "cancelled")["progress"] == 0.25
        for path, headers in [("/api/operations/events?since=3", {}),
                              ("/api/operations/events", {"Last-Event-ID": "3"})]:
            with connection(service) as conn:
                conn.request("GET", path, headers=headers)
                stream = conn.getresponse()
                assert read_event(stream)[0] == 4
                assert read_event(stream)[0] == last_seq
        before = service.operations.events_since()
        assert post(service, f"/api/operations/{op_id}/cancel", csrf=csrf)[0] == 200
        assert service.operations.events_since() == before


def test_queued_cancel_never_runs_job_and_unknown_cancel_is_404(service):
    ran = Event()
    # Hold the same lifecycle lock while submitting and cancelling to make the
    # queued cancellation deterministic, before the worker can start.
    with service._job_lock:
        op_id = service.submit("check", lambda context: ran.set())
        service.cancel(op_id)
    assert wait_state(service, op_id, "cancelled")["progress"] == 0
    assert not ran.is_set()
    assert post(service, "/api/operations/unknown/cancel")[0] == 404


def test_job_failure_is_reported_without_exception_details():
    runtime = FakeRuntime(fail_on={"devices": RuntimeError("private detail")})
    with running(runtime=runtime) as service:
        status, _, body = post(service, body='{"kind":"devices"}')
        assert status == 202
        operation = wait_state(service, json.loads(body)["id"], "failed")
        assert operation["message"] == "job failed" and operation["detail"] is None


@pytest.mark.parametrize("body", ["bad", "[]", "null", "{}", '{"kind":[]}',
                                 '{"kind":"unknown"}', '{"kind":"devices","extra":1}'])
def test_invalid_job_input_does_not_run(service, body):
    assert post(service, body=body)[0] == 400
    assert service.operations.events_since() == []


@pytest.mark.parametrize("query", ["since=-1", "since=bad", "since=1&since=2", "bad=1"])
def test_invalid_cursor(service, query):
    assert request(service, "GET", "/api/operations/events?" + query)[0] == 400


def test_cli_runs_fake_service_on_free_port():
    command = [sys.executable, "-m", "workstation", "serve", "--fake", "--port", "0"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = Queue()
    Thread(target=lambda: output.put(process.stdout.readline()), daemon=True).start()
    try:
        line = output.get(timeout=5)
        match = re.fullmatch(r"Mission Control: http://127\.0\.0\.1:(\d+)\n", line)
        assert match, line
        with closing(HTTPConnection("127.0.0.1", int(match[1]), timeout=3)) as conn:
            conn.request("GET", "/")
            response = conn.getresponse()
            assert response.status == 200
            csrf = re.search(rb'name="csrf-token" content="([^"]+)"', response.read())[1]
        with closing(HTTPConnection("127.0.0.1", int(match[1]), timeout=3)) as conn:
            conn.request("POST", "/api/operations", body='{"kind":"devices"}',
                         headers={"X-CSRF-Token": csrf.decode(),
                                  "Content-Type": "application/json"})
            response = conn.getresponse()
            assert response.status == 202
            op_id = json.loads(response.read())["id"]
        # The fake runtime's device result is empty, and no real runtime is constructed.
        class ServiceAddress:
            server_port = int(match[1])
        assert wait_state(ServiceAddress(), op_id, "succeeded")["detail"] == {}
    finally:
        process.terminate()
        process.communicate(timeout=5)


def test_cli_requires_explicit_runtime_and_lan_flag():
    with pytest.raises(SystemExit) as exc:
        main(["serve"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        main(["serve", "--fake", "--host", "0.0.0.0"])
    assert exc.value.code == 2


def test_server_close_requests_cancellation(service):
    op_id = service.operations.create("devices")
    service.operations.start(op_id)
    service.server_close()
    assert service.operations.cancel_requested(op_id)
    assert service.stopping.is_set()
    with pytest.raises(RuntimeError, match="stopping"):
        service.submit("check", lambda context: None)


def test_server_close_ends_open_event_stream(service):
    with connection(service) as conn:
        conn.request("GET", "/api/operations/events")
        response = conn.getresponse()
        assert response.status == 200
        service.shutdown()
        service.server_close()
        assert b"data:" not in response.read()
