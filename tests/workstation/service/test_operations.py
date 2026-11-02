"""Locked tests for #36 (workstation/service/operations.py). One test per Expectation sentence."""

import re

import pytest

from workstation.errors import InvalidTransition
from workstation.service.operations import OperationRegistry


def make():
    ticks = iter(f"2026-11-02T00:00:{i:02d}Z" for i in range(60))
    return OperationRegistry(clock=lambda: next(ticks))


def test_e1_ids_and_get_shape():
    reg = make()
    a = reg.create("pull", message="queued", detail={"image": "x"})
    b = reg.create("pull")
    assert (a, b) == ("op-000001", "op-000002")
    assert reg.get(a) == {"id": a, "kind": "pull", "state": "queued", "progress": 0.0,
                          "message": "queued", "detail": {"image": "x"},
                          "created_at": "2026-11-02T00:00:00Z",
                          "updated_at": "2026-11-02T00:00:00Z"}


def test_e2_get_returns_copy_and_unknown_raises():
    reg = make()
    a = reg.create("pull", detail={"image": "x"})
    got = reg.get(a)
    got["state"] = "running"
    got["detail"]["image"] = "y"
    assert reg.get(a)["state"] == "queued" and reg.get(a)["detail"] == {"image": "x"}
    with pytest.raises(KeyError):
        reg.get("op-999999")


def test_e3_start_and_progress():
    reg = make()
    a = reg.create("pull")
    with pytest.raises(InvalidTransition):
        reg.progress(a, 0.5)
    reg.start(a)
    reg.progress(a, 0.25, message="a quarter")
    op = reg.get(a)
    assert op["state"] == "running" and op["progress"] == 0.25 and op["message"] == "a quarter"
    with pytest.raises(InvalidTransition):
        reg.start(a)


def test_e4_progress_bounds():
    reg = make()
    a = reg.create("pull")
    reg.start(a)
    for bad in (-0.1, 1.5):
        with pytest.raises(ValueError, match="^fraction must be between 0 and 1$"):
            reg.progress(a, bad)


def test_e5_finish():
    reg = make()
    a, b = reg.create("pull"), reg.create("pull")
    reg.start(a)
    reg.start(b)
    reg.progress(b, 0.4)
    reg.finish(a, ok=True)
    reg.finish(b, ok=False, message="disk full")
    assert reg.get(a)["state"] == "succeeded" and reg.get(a)["progress"] == 1.0
    assert reg.get(b)["state"] == "failed" and reg.get(b)["message"] == "disk full"
    with pytest.raises(InvalidTransition):
        reg.finish(a, ok=True)


def test_e6_cancel():
    reg = make()
    q, r, done = reg.create("pull"), reg.create("pull"), reg.create("pull")
    reg.start(r)
    reg.start(done)
    reg.finish(done, ok=True)
    reg.cancel(q)
    reg.cancel(r)
    before = len(reg.events_since(0))
    reg.cancel(done)
    reg.cancel(q)
    assert len(reg.events_since(0)) == before
    assert reg.get(q)["state"] == "cancelled"
    assert reg.get(r)["state"] == "cancelling" and reg.cancel_requested(r) is True
    assert reg.get(done)["state"] == "succeeded" and reg.cancel_requested(done) is False


def test_e7_acknowledge_cancel_and_progress_while_cancelling():
    reg = make()
    a = reg.create("pull")
    with pytest.raises(InvalidTransition):
        reg.acknowledge_cancel(a)
    reg.start(a)
    reg.cancel(a)
    reg.progress(a, 0.9)
    reg.acknowledge_cancel(a)
    assert reg.get(a)["state"] == "cancelled" and reg.cancel_requested(a) is False


def test_e8_events():
    reg = make()
    a = reg.create("pull", message="m")
    reg.start(a)
    reg.progress(a, 0.5)
    events = reg.events_since(0)
    assert [e["seq"] for e in events] == [1, 2, 3]
    assert events[2] == {"seq": 3, "op_id": a, "state": "running", "progress": 0.5,
                         "message": "m", "at": "2026-11-02T00:00:02Z"}
    assert [e["seq"] for e in reg.events_since(2)] == [3]
    events[0]["state"] = "tampered"
    assert reg.events_since(0)[0]["state"] == "queued"


def test_e9_default_clock_is_utc_string():
    reg = OperationRegistry()
    a = reg.create("pull")
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", reg.get(a)["created_at"])
