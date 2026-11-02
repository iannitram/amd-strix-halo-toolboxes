"""Drain or defer a promotion while requests are active (R2). Planned: #23."""


def wait_for_idle(runtime, handle, *, timeout_s: float, poll_s: float = 0.5) -> bool:
    raise NotImplementedError("TODO #23")
