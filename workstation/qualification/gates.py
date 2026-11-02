"""Turn check results into one qualification decision (R3)."""

CHECK_STATUSES = ("passed", "failed", "unknown")


def decide(checks) -> str:
    """Return "passed", "failed" or "unqualified" for a list of check results."""
    required_statuses = []
    for check in checks:
        name = check["name"]
        status = check["status"]
        if status not in CHECK_STATUSES:
            raise ValueError(f"bad status for {name}: {status}")
        if check.get("required", True):
            required_statuses.append(status)

    if "failed" in required_statuses:
        return "failed"
    if not required_statuses or "unknown" in required_statuses:
        return "unqualified"
    return "passed"
