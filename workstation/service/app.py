"""Standard-library local service. Recipe, plan and update routes belong to #37.

POST /api/operations accepts {"kind": "devices"} for a read-only runtime check.
Jobs receive a JobContext and must check cancellation between bounded steps.
GET /api/operations/events is SSE; reconnect with Last-Event-ID or ?since=N.
"""

import json
import secrets
import socket
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from threading import Event, RLock, Thread
from urllib.parse import parse_qs, urlsplit

from workstation.service.operations import OperationRegistry
from workstation.service.security import DEFAULT_ALLOWED_HOSTS, check_request

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
ASSETS = {"/styles.css": ("styles.css", "text/css"),
          "/app.js": ("app.js", "text/javascript")}


class JobCancelled(Exception):
    """Cooperative cancellation at a job's next checkpoint."""


class JobContext:
    def __init__(self, service, op_id):
        self.runtime = service.runtime
        self.operations = service.operations
        self.op_id = op_id

    def check_cancelled(self):
        if self.operations.cancel_requested(self.op_id):
            raise JobCancelled()

    def progress(self, fraction, *, message=None):
        self.check_cancelled()
        self.operations.progress(self.op_id, fraction, message=message)


def _devices(context):
    context.check_cancelled()
    return context.runtime.devices()


class LocalService(ThreadingHTTPServer):
    """Use create_server(), then serve_forever()/shutdown() for embedded use."""

    daemon_threads = True

    def __init__(self, address, *, runtime, data_dir, allowed_hosts, jobs):
        if ":" in address[0]:
            self.address_family = socket.AF_INET6
        self.runtime = runtime
        self.data_dir = data_dir
        self.allowed_hosts = frozenset(allowed_hosts)
        self.csrf_token = secrets.token_urlsafe(32)
        self.operations = OperationRegistry()
        self.jobs = dict(jobs)
        self.stopping = Event()
        self._job_lock = RLock()
        super().__init__(address, _Handler)

    def server_bind(self):
        # HTTPServer's default reverse DNS lookup is unnecessary here.
        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]

    def submit(self, kind, job):
        """Return immediately; job(context) runs on a daemon worker thread."""
        with self._job_lock:
            if self.stopping.is_set():
                raise RuntimeError("service is stopping")
            op_id = self.operations.create(kind)
            Thread(target=self._run_job, args=(op_id, job), daemon=True).start()
            return op_id

    def _run_job(self, op_id, job):
        with self._job_lock:
            if self.operations.get(op_id)["state"] == "cancelled":
                return
            self.operations.start(op_id)
        try:
            result = job(JobContext(self, op_id))
            # Validate before storing a result that the JSON API cannot deliver.
            json.dumps(result, allow_nan=False)
        except JobCancelled:
            result, ok, message = None, False, "cancelled"
        except Exception:
            # Exception text can contain credentials or private paths.
            result, ok, message = None, False, "job failed"
        else:
            ok, message = True, "completed"
        with self._job_lock:
            if self.operations.cancel_requested(op_id):
                self.operations.acknowledge_cancel(op_id)
            else:
                self.operations.finish(op_id, ok=ok, message=message, detail=result)

    def cancel(self, op_id):
        with self._job_lock:
            self.operations.cancel(op_id)
            return self.operations.get(op_id)

    def server_close(self):
        with self._job_lock:
            self.stopping.set()
            for op_id in {event["op_id"] for event in self.operations.events_since()}:
                self.operations.cancel(op_id)
        super().server_close()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):
        # Request paths and client addresses must not leak into default logs.
        pass

    def _refusal(self):
        reason = check_request(self.command, self.headers,
                               csrf_token=self.server.csrf_token,
                               allowed_hosts=self.server.allowed_hosts)
        if reason:
            return reason
        for name in ("Host", "Origin", "Sec-Fetch-Site", "X-CSRF-Token"):
            if len(self.headers.get_all(name, [])) > 1:
                return "duplicate security header"
        return None

    def parse_request(self):
        if not super().parse_request():
            return False
        reason = self._refusal()
        if reason:
            self._json(403, {"error": reason})
            return False
        try:
            self.target = urlsplit(self.path)
        except ValueError:
            self._json(400, {"error": "invalid request target"})
            return False
        return True

    def handle_expect_100(self):
        reason = self._refusal()
        if reason:
            self._json(403, {"error": reason})
            return False
        return super().handle_expect_100()

    def send_error(self, code, message=None, explain=None):
        self._json(code, {"error": self.responses.get(code, ("request failed",))[0]})

    def _headers(self, status, content_type, length=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
        self.send_header("Connection", "close")
        if length is not None:
            self.send_header("Content-Length", str(length))
        self.end_headers()
        self.close_connection = True

    def _reply(self, status, body, content_type):
        self._headers(status, content_type, len(body))
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status, value):
        self._reply(status, json.dumps(value, allow_nan=False).encode(), "application/json")

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self._headers(204, "application/json", 0)

    def do_GET(self):
        target = self.target
        if target.path in ("/", "/index.html"):
            page = (WEB_DIR / "index.html").read_text(encoding="utf-8")
            bootstrap = f'<meta name="csrf-token" content="{escape(self.server.csrf_token)}">'
            self._reply(200, page.replace("<head>", "<head>\n  " + bootstrap, 1).encode(),
                        "text/html; charset=utf-8")
        elif target.path in ASSETS:
            name, content_type = ASSETS[target.path]
            self._reply(200, (WEB_DIR / name).read_bytes(), content_type + "; charset=utf-8")
        elif target.path == "/api/operations/events":
            self._events(target.query)
        elif target.path.startswith("/api/operations/"):
            try:
                operation = self.server.operations.get(target.path.removeprefix("/api/operations/"))
            except KeyError:
                self._json(404, {"error": "unknown operation"})
            else:
                self._json(200, operation)
        else:
            self._json(404, {"error": "not found"})

    def _events(self, query):
        try:
            # Python 3.10 rejects an empty query when strict parsing is enabled.
            values = parse_qs(query, strict_parsing=True) if query else {}
            raw = values.get("since", [self.headers.get("Last-Event-ID", "0")])
            if set(values) - {"since"} or len(raw) != 1:
                raise ValueError()
            seq = int(raw[0])
            if seq < 0:
                raise ValueError()
        except ValueError:
            self._json(400, {"error": "invalid event cursor"})
            return
        self._headers(200, "text/event-stream")
        if self.command == "HEAD":
            return
        try:
            while not self.server.stopping.is_set():
                events = self.server.operations.events_since(seq)
                for event in events:
                    seq = event["seq"]
                    frame = f"id: {seq}\nevent: operation\ndata: {json.dumps(event)}\n\n"
                    self.wfile.write(frame.encode())
                if not events:
                    self.wfile.write(b": keep-alive\n\n")
                self.wfile.flush()
                self.server.stopping.wait(0.1)
        except OSError:
            pass  # A disconnected page reconnects using its last event id.

    def do_POST(self):
        path = self.target.path
        if path.startswith("/api/operations/") and path.endswith("/cancel"):
            op_id = path[len("/api/operations/"):-len("/cancel")]
            try:
                operation = self.server.cancel(op_id)
            except KeyError:
                self._json(404, {"error": "unknown operation"})
            else:
                self._json(200, operation)
            return
        if path != "/api/operations":
            self._json(404, {"error": "not found"})
            return
        try:
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or self.headers.get("Transfer-Encoding"):
                raise ValueError()
            length = int(lengths[0])
            if not 0 < length <= 65536:
                raise ValueError()
            if self.headers.get_content_type() != "application/json":
                raise ValueError()
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError()
            payload = json.loads(body)
            if not isinstance(payload, dict) or set(payload) != {"kind"}:
                raise ValueError()
            kind = payload["kind"]
            if not isinstance(kind, str) or kind not in self.server.jobs:
                raise ValueError()
        except (ValueError, OSError):
            self._json(400, {"error": "expected a JSON object with a supported job kind"})
            return
        op_id = self.server.submit(kind, self.server.jobs[kind])
        self._json(202, {"id": op_id})


def create_server(*, host="127.0.0.1", port=8765, runtime=None, data_dir=None,
                  allow_lan=False, allowed_hosts=DEFAULT_ALLOWED_HOSTS, jobs=None):
    """Bind a service without starting its loop; port=0 chooses a free port.

    Any address except 127.0.0.1 requires allow_lan=True. LAN host names must
    also be explicitly included in allowed_hosts; binding never widens it.
    A runtime is required so fake execution cannot be mistaken for real work.
    """
    if host != "127.0.0.1" and not allow_lan:
        raise ValueError("another bind address requires allow_lan=True")
    if runtime is None:
        raise ValueError("an explicit runtime is required (use --fake for the demo)")
    return LocalService((host, port), runtime=runtime, data_dir=data_dir,
                        allowed_hosts=allowed_hosts, jobs={"devices": _devices} if jobs is None
                        else jobs)


def serve(*, host="127.0.0.1", port=8765, runtime=None, data_dir=None,
          allow_lan=False, allowed_hosts=DEFAULT_ALLOWED_HOSTS, jobs=None):
    """Bind and run until interrupted; embedded callers can use create_server()."""
    with create_server(host=host, port=port, runtime=runtime, data_dir=data_dir,
                       allow_lan=allow_lan, allowed_hosts=allowed_hosts, jobs=jobs) as server:
        address, port = server.server_address[:2]
        if ":" in address:
            address = f"[{address}]"
        print(f"Mission Control: http://{address}:{port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
