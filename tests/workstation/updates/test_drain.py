"""Drain tests use an in-memory runtime and advance only simulated time."""

import pytest

from workstation.runtime.fake import FakeRuntime
from workstation.updates import drain


class FakeClock:
    def __init__(self):
        self.now = 100.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(drain, "monotonic", clock.monotonic)
    monkeypatch.setattr(drain, "sleep", clock.sleep)
    return clock


@pytest.mark.parametrize("timeout_s", [0, 5])
def test_already_idle_returns_true_without_sleeping(clock, timeout_s):
    runtime = FakeRuntime()
    handle = runtime.start_server({})

    assert drain.wait_for_idle(runtime, handle, timeout_s=timeout_s) is True
    assert clock.sleeps == []
    assert handle["id"] in runtime.servers


def test_polls_supplied_handle_until_requests_finish(clock, monkeypatch):
    runtime = FakeRuntime(active_requests=2)
    handle = runtime.start_server({})
    polls = []
    active_requests = runtime.active_requests

    def poll(current_handle):
        polls.append((current_handle, active_requests(current_handle)))
        return polls[-1][1]

    def sleep(seconds):
        clock.sleep(seconds)
        runtime.active_requests_result -= 1

    monkeypatch.setattr(runtime, "active_requests", poll)
    monkeypatch.setattr(drain, "sleep", sleep)

    assert drain.wait_for_idle(runtime, handle, timeout_s=5) is True
    assert polls == [(handle, 2), (handle, 1), (handle, 0)]
    assert clock.sleeps == [0.5, 0.5]
    assert handle["id"] in runtime.servers


@pytest.mark.parametrize(
    ("timeout_s", "poll_s", "sleeps"),
    [(0, 0.5, []), (1.25, 0.5, [0.5, 0.5, 0.25]), (0.25, 2, [0.25])],
)
def test_busy_server_times_out_without_oversleeping(clock, timeout_s, poll_s, sleeps):
    runtime = FakeRuntime(active_requests=1)
    handle = runtime.start_server({})

    assert drain.wait_for_idle(runtime, handle, timeout_s=timeout_s, poll_s=poll_s) is False
    assert clock.sleeps == sleeps
    assert clock.now == 100 + timeout_s
    assert handle["id"] in runtime.servers
    assert runtime.active_requests(handle) == 1


def test_checks_for_idle_at_deadline(clock, monkeypatch):
    runtime = FakeRuntime(active_requests=1)
    handle = runtime.start_server({})

    def sleep(seconds):
        clock.sleep(seconds)
        if clock.now == 101:
            runtime.active_requests_result = 0

    monkeypatch.setattr(drain, "sleep", sleep)

    assert drain.wait_for_idle(runtime, handle, timeout_s=1, poll_s=0.75) is True
    assert clock.sleeps == [0.75, 0.25]


def test_poll_duration_counts_towards_timeout(clock, monkeypatch):
    runtime = FakeRuntime(active_requests=1)
    handle = runtime.start_server({})
    active_requests = runtime.active_requests

    def poll(current_handle):
        clock.now += 0.25
        return active_requests(current_handle)

    monkeypatch.setattr(runtime, "active_requests", poll)

    assert drain.wait_for_idle(runtime, handle, timeout_s=1) is False
    assert clock.sleeps == [0.5]
    assert clock.now == 101


def test_request_count_failure_propagates_without_stopping_server(clock):
    runtime = FakeRuntime(fail_on={"active_requests"})
    handle = runtime.start_server({})

    with pytest.raises(RuntimeError, match="failure at active_requests"):
        drain.wait_for_idle(runtime, handle, timeout_s=1)

    assert clock.sleeps == []
    assert handle["id"] in runtime.servers


@pytest.mark.parametrize("timeout_s", [-1, float("inf"), float("nan")])
def test_rejects_invalid_timeout(clock, timeout_s):
    with pytest.raises(ValueError, match="timeout_s"):
        drain.wait_for_idle(FakeRuntime(), {}, timeout_s=timeout_s)
    assert clock.sleeps == []


@pytest.mark.parametrize("poll_s", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_poll_interval(clock, poll_s):
    with pytest.raises(ValueError, match="poll_s"):
        drain.wait_for_idle(FakeRuntime(), {}, timeout_s=1, poll_s=poll_s)
    assert clock.sleeps == []
