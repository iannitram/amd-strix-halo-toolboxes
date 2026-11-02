"""GGUF metadata before download, with HTTP range requests (P1). Planned: #31."""


def read_remote(url: str, *, fetch_range=None, max_bytes: int = 16 * 1024 * 1024) -> dict:
    raise NotImplementedError("TODO #31")
