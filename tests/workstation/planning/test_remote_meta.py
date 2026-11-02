"""Remote GGUF tests inject transports; no default test uses the network."""

import struct
import urllib.error

import pytest

from workstation.planning import remote_meta
from workstation.planning.gguf_meta import read_local
from workstation.planning.remote_meta import read_remote


URL = "https://example.invalid/model.gguf"


def _string(value):
    encoded = value.encode("utf-8")
    return struct.pack("<Q", len(encoded)) + encoded


def _gguf(metadata):
    entries = []
    for key, value in metadata:
        if isinstance(value, str):
            encoded = struct.pack("<I", 8) + _string(value)
        else:
            encoded = struct.pack("<II", 4, value)
        entries.append(_string(key) + encoded)
    return struct.pack("<IIQQ", 0x46554747, 3, 1, len(metadata)) + b"".join(entries)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail("tests must not use the network")

    monkeypatch.setattr(remote_meta.urllib.request, "urlopen", fail)


def _fetch(data, calls):
    def fetch(url, start, end):
        calls.append((url, start, end))
        last = min(end, len(data) - 1)
        return 206, {"Content-Range": f"bytes {start}-{last}/{len(data)}"}, data[start:last + 1]

    return fetch


def _assert_unknown(result):
    assert result["reason"]
    assert all(value is None for key, value in result.items() if key != "reason")


@pytest.mark.parametrize("extra", [
    [],
    [("llama.attention.sliding_window_size", 4096)],
    [("general.name", "Scout")],
])
def test_matches_local_fields_and_fetches_only_metadata(tmp_path, extra):
    header = _gguf([
        ("general.architecture", "llama"),
        ("llama.block_count", 32),
        ("llama.attention.head_count_kv", 8),
        ("llama.attention.key_length", 128),
        ("llama.attention.value_length", 128),
        *extra,
    ])
    # A tensor descriptor and weights follow the metadata; neither is needed.
    data = header + b"tensor-info-and-weights" * 100
    model = tmp_path / "model.gguf"
    model.write_bytes(data)
    expected = read_local(model)
    expected["file_sizes_bytes"] = {URL: len(data)}
    calls = []

    assert read_remote(URL, fetch_range=_fetch(data, calls), max_bytes=len(header)) == expected
    assert calls[0] == (URL, 0, 23)
    assert all(0 <= start <= end < len(header) for _, start, end in calls)
    assert sum(end - start + 1 for _, start, end in calls) == len(header)


def test_missing_metadata_stays_none():
    data = _gguf([("general.architecture", "llama")])
    result = read_remote(URL, fetch_range=_fetch(data, []))

    assert result["architecture"] == "llama"
    for key in ("n_layers", "n_head_kv", "key_length", "value_length", "sliding_window_size"):
        assert result[key] is None
    assert result["total_size_bytes"] == len(data)


def test_skips_unneeded_arrays_without_fetching_their_contents():
    # A fixed-width array can be skipped in one step; string lengths are read,
    # but their contents are skipped. Architectural fields after both still work.
    fixed_key = _string("unused.array") + struct.pack("<IIQ", 9, 4, 100)
    fixed_data = b"x" * 400
    strings = (
        _string("unused.strings") + struct.pack("<IIQ", 9, 8, 2)
        + _string("abc") + _string("defgh")
    )
    fields = _gguf([("general.architecture", "llama"), ("llama.block_count", 7)])[24:]
    header = struct.pack("<IIQQ", 0x46554747, 3, 0, 4)
    data = header + fixed_key + fixed_data + strings + fields
    calls = []

    result = read_remote(URL, fetch_range=_fetch(data, calls), max_bytes=len(data))

    assert result["n_layers"] == 7
    skipped_start = len(header + fixed_key)
    assert all(end < skipped_start or start >= skipped_start + 400 for _, start, end in calls)
    assert sum(end - start + 1 for _, start, end in calls) == len(data) - 408


@pytest.mark.parametrize("limit", [0, 23, 24, 40, 100])
def test_header_budget_never_exceeded(limit):
    data = _gguf([("general.architecture", "llama"), ("llama.block_count", 32)])
    calls = []

    result = read_remote(URL, fetch_range=_fetch(data, calls), max_bytes=limit)

    _assert_unknown(result)
    assert "max_bytes" in result["reason"]
    assert all(end < limit for _, _, end in calls)
    assert sum(end - start + 1 for _, start, end in calls) <= limit


def test_skipped_values_are_also_bounded_by_max_bytes():
    data = (
        struct.pack("<IIQQ", 0x46554747, 3, 0, 1)
        + _string("unused") + struct.pack("<IIQ", 9, 4, 1000) + b"x" * 4000
    )
    calls = []
    result = read_remote(URL, fetch_range=_fetch(data, calls), max_bytes=100)

    _assert_unknown(result)
    assert "max_bytes" in result["reason"]
    assert all(end < 100 for _, _, end in calls)


@pytest.mark.parametrize(("status", "headers", "body", "reason"), [
    (200, {}, b"whole file", "206 required"),
    (404, {}, b"", "206 required"),
    (416, {}, b"", "206 required"),
    (206, {}, b"", "Content-Range"),
    (206, {"Content-Range": "bytes 0-23/*"}, b"", "unknown file size"),
    (206, {"Content-Range": "bytes 1-24/100"}, b"x" * 24, "mismatched"),
    (206, {"Content-Range": "bytes 0-22/100"}, b"x" * 23, "mismatched"),
    (206, {"Content-Range": "bytes 0-23/100"}, b"x" * 23, "truncated"),
    (206, {"Content-Range": "bytes 0-23/100"}, b"x" * 25, "oversized"),
    (206, {"Content-Range": "bytes 0-23/100", "Content-Encoding": "gzip"}, b"", "encoded"),
])
def test_invalid_range_responses_are_unknown(status, headers, body, reason):
    result = read_remote(URL, fetch_range=lambda *_: (status, headers, body))

    _assert_unknown(result)
    assert reason in result["reason"]


@pytest.mark.parametrize("after", [0, 6])
def test_network_errors_discard_partial_metadata_without_private_details(after):
    data = _gguf([("general.architecture", "llama"), ("llama.block_count", 32)])
    calls = []
    fetch = _fetch(data, calls)

    def fail(url, start, end):
        if len(calls) == after:
            raise OSError("private transport details")
        return fetch(url, start, end)

    result = read_remote(URL, fetch_range=fail)

    _assert_unknown(result)
    assert result["reason"] == "could not fetch remote GGUF metadata"
    assert len(calls) == after


def test_rejects_changing_file_sizes():
    data = _gguf([("general.architecture", "llama")])
    calls = []
    fetch = _fetch(data, calls)

    def changing(url, start, end):
        status, headers, body = fetch(url, start, end)
        if start:
            headers["Content-Range"] = f"bytes {start}-{end}/{len(data) + 1}"
        return status, headers, body

    result = read_remote(URL, fetch_range=changing)
    _assert_unknown(result)
    assert "size changed" in result["reason"]


@pytest.mark.parametrize("data", [
    b"short",
    struct.pack("<IIQQ", 0, 3, 0, 0),
    struct.pack("<IIQQ", 0x46554747, 3, 0, 1) + struct.pack("<Q", 2**63),
    struct.pack("<IIQQ", 0x46554747, 3, 0, 1) + _string("x") + struct.pack("<I", 99),
    _gguf([("general.architecture", 5)]),
])
def test_malformed_gguf_is_unknown(data):
    _assert_unknown(read_remote(URL, fetch_range=_fetch(data, [])))


def test_split_file_does_not_guess_other_shard_sizes():
    data = _gguf([("general.architecture", "llama")])
    url = URL.replace("model.gguf", "model-00001-of-00002.gguf") + "?download=1"
    calls = []

    result = read_remote(url, fetch_range=_fetch(data, calls))

    assert result["architecture"] == "llama"
    assert result["file_sizes_bytes"] == {url: len(data)}
    assert result["total_size_bytes"] is None
    assert "other shards" in result["reason"]
    assert all(request_url == url for request_url, _, _ in calls)


class _Response:
    def __init__(self, status, headers, data):
        self.status, self.headers, self.data = status, headers, data
        self.reads = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def read(self, size):
        self.reads.append(size)
        return self.data[:size]


def test_http_adapter_requests_identity_ranges_and_bounds_reads(monkeypatch):
    data = _gguf([("general.architecture", "llama")])
    responses = []

    def urlopen(request, *, timeout):
        assert request.full_url == URL
        assert request.get_header("Accept-encoding") == "identity"
        assert timeout == 15
        start, end = map(int, request.get_header("Range").removeprefix("bytes=").split("-"))
        response = _Response(
            206, {"content-range": f"bytes {start}-{end}/{len(data)}"}, data[start:end + 1]
        )
        responses.append(response)
        return response

    monkeypatch.setattr(remote_meta.urllib.request, "urlopen", urlopen)
    assert read_remote(URL)["architecture"] == "llama"
    assert all(response.closed and len(response.reads) == 1 for response in responses)
    assert sum(sum(response.reads) for response in responses) == len(data)


@pytest.mark.parametrize(("status", "headers"), [
    (200, {}),
    (206, {}),
    (206, {"Content-Range": "bytes 0-99/100"}),
    (206, {"Content-Range": "bytes 0-23/100", "Content-Encoding": "gzip"}),
])
def test_http_adapter_never_reads_unsupported_response_bodies(monkeypatch, status, headers):
    response = _Response(status, headers, b"weights" * 100)
    monkeypatch.setattr(remote_meta.urllib.request, "urlopen", lambda *_a, **_k: response)

    _assert_unknown(read_remote(URL))
    assert response.closed
    assert response.reads == []


def test_http_error_body_is_not_downloaded(monkeypatch):
    response = _Response(404, {}, b"error body")

    def fail(*args, **kwargs):
        raise urllib.error.HTTPError(URL, 404, "missing", {}, response)

    monkeypatch.setattr(remote_meta.urllib.request, "urlopen", fail)
    _assert_unknown(read_remote(URL))
    assert response.reads == []
