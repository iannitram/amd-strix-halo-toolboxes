"""Locked tests for #29 (workstation/planning/labels.py). One test per Expectation sentence."""

import pytest

from workstation.planning.labels import label_value

NOW = "2026-11-02T12:00:00Z"


def test_e1_unknown_source_checked_first():
    with pytest.raises(ValueError, match="^unknown source: guess$"):
        label_value(None, source="guess")


def test_e2_none_is_unknown():
    assert label_value(None, source="measured", observed_at=NOW, now=NOW) == {
        "value": None, "label": "unknown", "source": "measured", "age_s": None}


def test_e3_estimate():
    assert label_value(5, source="estimate", observed_at=NOW, now=NOW) == {
        "value": 5, "label": "estimated", "source": "estimate", "age_s": None}


def test_e4_measured_fresh_and_boundary():
    out = label_value(7, source="measured", observed_at="2026-11-02T11:55:00Z", now=NOW)
    assert out == {"value": 7, "label": "measured", "source": "measured", "age_s": 300}
    out = label_value(7, source="measured", observed_at="2026-11-02T11:59:59.5+00:00", now=NOW)
    assert out["age_s"] == 0 and out["label"] == "measured"


def test_e5_measured_stale():
    out = label_value(7, source="measured", observed_at="2026-11-02T11:54:59Z", now=NOW)
    assert out["label"] == "stale" and out["age_s"] == 301
    out = label_value(7, source="measured", observed_at="2026-11-02T11:59:00Z", now=NOW,
                      stale_after_s=30)
    assert out["label"] == "stale" and out["age_s"] == 60


def test_e6_missing_times_are_stale():
    assert label_value(1, source="measured", now=NOW)["label"] == "stale"
    out = label_value(1, source="measured", observed_at=NOW)
    assert out["label"] == "stale" and out["age_s"] is None
