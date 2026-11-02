"""Which images to keep and which to remove (R2). Planned: #21."""


def plan_gc(artifacts, *, active, previous=None, pinned=frozenset(), keep_recent=0) -> dict:
    """Return {"keep": [...], "remove": [...], "reasons": {id: reason}}; removes nothing itself."""
    raise NotImplementedError("TODO #21")
