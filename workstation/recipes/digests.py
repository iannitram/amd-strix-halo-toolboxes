"""Resolve a mutable image tag to its immutable digest (R1). Planned: #19.

Uses the OCI distribution API over HTTPS (works from any OS); ``fetch`` is injectable for tests.
"""


def resolve_digest(repository: str, tag: str, *, fetch=None) -> str:
    """Return ``sha256:<64 hex>`` for ``repository:tag``; else WorkstationError."""
    raise NotImplementedError("TODO #19")
