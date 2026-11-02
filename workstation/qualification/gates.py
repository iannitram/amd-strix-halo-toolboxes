"""Turn check results into one qualification decision (R3). Planned: #25."""

CHECK_STATUSES = ("passed", "failed", "unknown")


def decide(checks) -> str:
    """Return "passed", "failed" or "unqualified" for a list of check results."""
    raise NotImplementedError("TODO #25")
