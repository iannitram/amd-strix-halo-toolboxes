"""Which images to keep and which to remove (R2). Planned: #21."""


def plan_gc(artifacts, *, active, previous=None, pinned=frozenset(), keep_recent=0) -> dict:
    """Return {"keep": [...], "remove": [...], "reasons": {id: reason}}; removes nothing itself."""
    if keep_recent < 0:
        raise ValueError("keep_recent must be >= 0")

    artifact_ids = {artifact["id"] for artifact in artifacts}
    if active not in artifact_ids:
        raise ValueError(f"active artifact not found: {active}")

    reasons = {}
    for artifact in artifacts:
        artifact_id = artifact["id"]
        if artifact_id == active:
            reasons[artifact_id] = "active"
        elif artifact_id == previous:
            reasons[artifact_id] = "previous"
        elif artifact_id in pinned:
            reasons[artifact_id] = "pinned"

    recent_candidates = [
        artifact for artifact in artifacts if artifact["id"] not in reasons
    ]
    recent_candidates.sort(key=lambda artifact: artifact["id"])
    recent_candidates.sort(key=lambda artifact: artifact["created_at"], reverse=True)
    for artifact in recent_candidates[:keep_recent]:
        reasons[artifact["id"]] = "recent"

    keep = [artifact["id"] for artifact in artifacts if artifact["id"] in reasons]
    remove = [artifact["id"] for artifact in artifacts if artifact["id"] not in reasons]
    return {"keep": keep, "remove": remove, "reasons": reasons}
