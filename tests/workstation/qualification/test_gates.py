"""Locked tests for #25 (workstation/qualification/gates.py). One test per Expectation sentence."""

import copy

import pytest

from workstation.qualification.gates import decide


def c(name, status, required=True):
    return {"name": name, "status": status, "required": required}


def test_e1_bad_status():
    with pytest.raises(ValueError, match="^bad status for load: maybe$"):
        decide([c("load", "maybe")])


def test_e2_any_required_failure_fails():
    assert decide([c("load", "passed"), c("chat", "failed"), c("x", "unknown")]) == "failed"


def test_e3_no_required_or_unknown_is_unqualified():
    assert decide([]) == "unqualified"
    assert decide([c("a", "passed", False)]) == "unqualified"
    assert decide([c("a", "passed"), c("b", "unknown")]) == "unqualified"


def test_e4_all_required_passed():
    assert decide([c("a", "passed"), c("b", "passed")]) == "passed"


def test_e5_optional_ignored_and_required_defaults_true():
    assert decide([c("a", "passed"), c("b", "failed", False), c("d", "unknown", False)]) == "passed"
    assert decide([{"name": "a", "status": "failed"}]) == "failed"


def test_e6_input_unchanged():
    checks = [c("a", "passed"), c("b", "failed", False)]
    before = copy.deepcopy(checks)
    decide(checks)
    assert checks == before
