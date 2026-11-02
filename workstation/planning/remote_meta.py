"""GGUF metadata before download, with bounded HTTP range requests (P1)."""

import re
import struct
import urllib.error
import urllib.parse
import urllib.request

from workstation.planning.gguf_meta import _bounded_reader, _estimator, _metadata_result


_CONTENT_RANGE = re.compile(r"bytes (\d+)-(\d+)/(\d+)", re.IGNORECASE)


def _range_size(status, headers, start: int, end: int) -> int:
    """Validate range support before the HTTP adapter reads any response body."""
    if status != 206:
        raise ValueError("server did not return an HTTP byte range (206 required)")
    headers = {key.lower(): value for key, value in headers.items()}
    match = _CONTENT_RANGE.fullmatch(headers.get("content-range", ""))
    if not match:
        raise ValueError("server returned an invalid Content-Range or unknown file size")
    first, last, total = map(int, match.groups())
    if first != start or last != min(end, total - 1) or last < first:
        raise ValueError("server returned a mismatched Content-Range")
    if headers.get("content-encoding", "identity").lower() != "identity":
        raise ValueError("server returned encoded bytes instead of a GGUF byte range")
    return total


def _http_fetch_range(url: str, start: int, end: int) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(
        url, headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            headers = dict(response.headers.items())
            try:
                _range_size(response.status, headers, start, end)
            except ValueError:
                return response.status, headers, b""
            return response.status, headers, response.read(end - start + 1)
    except urllib.error.HTTPError as error:
        with error:
            return error.code, dict(error.headers.items()), b""


class _RangeStream:
    """A seekable metadata stream; skips and reads never pass the header budget.

    Fetch exactly what the parser requests, without read-ahead into tensor data.
    Skipped metadata values need no transfer, but still count toward max_bytes.
    """

    def __init__(self, url, fetch_range, max_bytes):
        self.url = url
        self.fetch_range = fetch_range
        self.max_bytes = max_bytes
        self.size = None
        self.position = 0

    def tell(self):
        return self.position

    def remaining(self):
        return self.size - self.position

    def _check(self, size):
        if self.position + size > self.max_bytes:
            raise ValueError("GGUF metadata header exceeds max_bytes")
        if self.size is not None and self.position + size > self.size:
            raise ValueError("truncated GGUF metadata header")

    def read(self, size):
        self._check(size)
        if not size:
            return b""
        start, end = self.position, self.position + size - 1
        try:
            status, headers, body = self.fetch_range(self.url, start, end)
        except Exception as error:
            raise ValueError("could not fetch remote GGUF metadata") from error
        total = _range_size(status, headers, start, end)
        if self.size is not None and total != self.size:
            raise ValueError("remote GGUF file size changed during metadata read")
        self.size = total
        if not isinstance(body, bytes) or len(body) != size:
            raise ValueError("truncated or oversized HTTP range response")
        self.position += size
        return body

    def seek(self, size, whence):
        if whence != 1 or size < 0:
            raise ValueError("invalid GGUF metadata seek")
        self._check(size)
        self.position += size


def read_remote(url: str, *, fetch_range=None, max_bytes: int = 16 * 1024 * 1024) -> dict:
    """Return the same metadata fields as read_local, using HTTP ranges only.

    ``fetch_range(url, start, end)`` uses inclusive byte offsets and returns
    ``(status, headers, body)``. The default urllib adapter bounds body reads and
    rejects servers without range support before reading their response bodies.
    ``max_bytes`` bounds the metadata header's extent, including skipped values.
    Only the supplied file is inspected; split-file totals remain unknown.
    Failures return None fields and a reason, never transport details or a URL.
    """
    unknown = dict.fromkeys(_metadata_result({}, {}))
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("remote GGUF URL must use HTTP or HTTPS")
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 24:
            raise ValueError("GGUF metadata header exceeds max_bytes (at least 24 required)")
        stream = _RangeStream(url, fetch_range or _http_fetch_range, max_bytes)
        reader_class = _bounded_reader(_estimator())

        class RemoteReader(reader_class):
            def _remaining(self):
                return stream.remaining()

        reader = RemoteReader(url)
        reader.f = stream
        magic, _, _, count = struct.unpack("<IIQQ", stream.read(24))
        if magic != 0x46554747:
            raise ValueError("invalid GGUF magic number")
        reader._read_metadata(count)
        result = _metadata_result(reader.metadata, {url: stream.size})
        # A single shard's size cannot establish the complete model's weight size.
        split_count = re.search(r"-\d{5}-of-(\d{5})\.gguf$", parsed.path, re.IGNORECASE)
        if split_count and int(split_count.group(1)) > 1:
            result["total_size_bytes"] = None
            result["reason"] = "split GGUF total size is unknown; other shards were not inspected"
        return result
    except (ValueError, struct.error) as error:
        # Parser messages are controlled; network exceptions are replaced above.
        return {**unknown, "reason": str(error)}
