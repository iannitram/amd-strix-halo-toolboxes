"""Locked tests for #21 (workstation/updates/retention.py). One test per Expectation sentence."""

import copy

import pytest

from workstation.updates.retention import plan_gc

ARTS = [
    {"id": "img-a", "created_at": "2026-10-01T00:00:00Z"},
    {"id": "img-b", "created_at": "2026-10-05T00:00:00Z"},
    {"id": "img-c", "created_at": "2026-10-03T00:00:00Z"},
    {"id": "img-d", "created_at": "2026-10-05T00:00:00Z"},
    {"id": "img-e", "created_at": "2026-10-02T00:00:00Z"},
]


def test_e1_inputs_unchanged_and_shape():
    arts = copy.deepcopy(ARTS)
    pinned = {"img-c"}
    out = plan_gc(arts, active="img-a", pinned=pinned)
    assert arts == ARTS and pinned == {"img-c"}
    assert set(out) == {"keep", "remove", "reasons"}


def test_e2_negative_keep_recent():
    with pytest.raises(ValueError, match="^keep_recent must be >= 0$"):
        plan_gc(ARTS, active="img-a", keep_recent=-1)


def test_e3_active_must_exist():
    with pytest.raises(ValueError, match="^active artifact not found: img-z$"):
        plan_gc(ARTS, active="img-z")


def test_e4_reasons_first_match_wins():
    out = plan_gc(ARTS, active="img-a", previous="img-a", pinned={"img-a", "img-e"})
    assert out["reasons"] == {"img-a": "active", "img-e": "pinned"}
    out = plan_gc(ARTS, active="img-a", previous="img-c", pinned={"img-c"})
    assert out["reasons"] == {"img-a": "active", "img-c": "previous"}


def test_e5_recent_newest_then_smaller_id():
    out = plan_gc(ARTS, active="img-a", keep_recent=2)
    assert out["reasons"] == {"img-a": "active", "img-b": "recent", "img-d": "recent"}
    out = plan_gc(ARTS, active="img-b", keep_recent=2)
    assert out["reasons"] == {"img-b": "active", "img-d": "recent", "img-c": "recent"}
    out = plan_gc(ARTS, active="img-d", keep_recent=1)
    assert out["reasons"] == {"img-d": "active", "img-b": "recent"}


def test_e6_keep_and_remove_in_input_order():
    out = plan_gc(ARTS, active="img-e", previous="img-b", keep_recent=1)
    assert out["keep"] == ["img-b", "img-d", "img-e"]
    assert out["remove"] == ["img-a", "img-c"]
    assert set(out["reasons"]) == set(out["keep"])


def test_e7_unknown_previous_and_pinned_ignored():
    out = plan_gc(ARTS, active="img-a", previous="img-x", pinned={"img-y"})
    assert out["keep"] == ["img-a"]
    assert out["remove"] == ["img-b", "img-c", "img-d", "img-e"]
