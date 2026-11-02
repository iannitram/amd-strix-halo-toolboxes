"""Drain or defer a promotion while requests are active (R2)."""

from math import isfinite
from time import monotonic, sleep

from workstation.runtime.port import RuntimePort


def wait_for_idle(
    runtime: RuntimePort, handle: dict, *, timeout_s: float, poll_s: float = 0.5
) -> bool:
    """Poll for zero active requests without stopping the server.

    Check immediately, even with a zero timeout, and once at the deadline.
    Runtime errors propagate so an unavailable request count cannot mean idle.
    """
    if not isfinite(timeout_s) or timeout_s < 0:
        raise ValueError("timeout_s must be finite and >= 0")
    if not isfinite(poll_s) or poll_s <= 0:
        raise ValueError("poll_s must be finite and > 0")

    deadline = monotonic() + timeout_s
    while True:
        if runtime.active_requests(handle) == 0:
            return True
        remaining = deadline - monotonic()
        if remaining <= 0:
            return False
        sleep(min(poll_s, remaining))
