"""Locked tests for #20 (workstation/updates/states.py). One test per Expectation sentence."""

import pytest

from workstation.errors import InvalidTransition
from workstation.updates.states import (
    STATES, TRANSITIONS, can_transition, is_settled, transition,
)

TABLE = {
    "resolving": {"pulling", "failed"},
    "pulling": {"staging", "failed"},
    "staging": {"checking", "failed"},
    "checking": {"candidate-ready", "failed"},
    "candidate-ready": {"promoting", "failed"},
    "promoting": {"active", "failed", "restoring"},
    "active": {"restoring"},
    "failed": {"restoring"},
    "restoring": {"active", "failed"},
}


def test_e1_table_exact_and_frozen():
    assert set(TRANSITIONS) == set(STATES)
    assert {k: set(v) for k, v in TRANSITIONS.items()} == TABLE
    assert all(isinstance(v, frozenset) for v in TRANSITIONS.values())


def test_e2_can_transition():
    assert can_transition("pulling", "staging") is True
    assert can_transition("pulling", "active") is False
    assert can_transition("nowhere", "active") is False
    assert can_transition("active", "nowhere") is False


def test_e3_unknown_state_current_first():
    with pytest.raises(ValueError, match="^unknown state: nowhere$"):
        transition("nowhere", "elsewhere")
    with pytest.raises(ValueError, match="^unknown state: elsewhere$"):
        transition("active", "elsewhere")


def test_e4_disallowed_move():
    with pytest.raises(InvalidTransition, match="^active -> promoting is not allowed$"):
        transition("active", "promoting")


def test_e5_allowed_move_returns_target():
    for current, targets in TABLE.items():
        for target in targets:
            assert transition(current, target) == target


def test_e6_is_settled():
    assert is_settled("active") is True
    assert is_settled("failed") is True
    for s in STATES:
        if s not in ("active", "failed"):
            assert is_settled(s) is False
    with pytest.raises(ValueError, match="^unknown state: x$"):
        is_settled("x")
