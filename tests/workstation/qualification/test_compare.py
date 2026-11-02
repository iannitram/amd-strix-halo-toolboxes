"""Locked tests for #26 (workstation/qualification/compare.py), one per Expectation."""

import copy

import pytest

from workstation.qualification.compare import compare_to_baseline

BASE = {"load_seconds": 10.0, "ttft_seconds": 0.5, "prefill_tps": 400.0, "decode_tps": 40.0}


def status(metric, value, threshold):
    return compare_to_baseline(BASE, {metric: value}, {metric: threshold})[0]["status"]


def test_e1_order_and_only_thresholded_metrics():
    rows = compare_to_baseline(BASE, dict(BASE), {"decode_tps": 5, "load_seconds": 5})
    assert [r["metric"] for r in rows] == ["load_seconds", "decode_tps"]


def test_e2_unknown_metric():
    with pytest.raises(ValueError, match="^unknown metric: vibes$"):
        compare_to_baseline(BASE, BASE, {"vibes": 1})


def test_e3_row_keys():
    rows = compare_to_baseline(BASE, BASE, {"decode_tps": 5})
    assert rows == [{"metric": "decode_tps", "baseline": 40.0, "candidate": 40.0,
                     "change_pct": 0.0, "threshold_pct": 5, "status": "passed"}]


def test_e4_missing_or_zero_is_unknown():
    rows = compare_to_baseline({"load_seconds": 0, "decode_tps": None},
                               {"load_seconds": 3.0, "decode_tps": 40.0, "ttft_seconds": 1.0},
                               {"load_seconds": 5, "decode_tps": 5, "ttft_seconds": 5})
    assert len(rows) == 3
    for r in rows:
        assert r["status"] == "unknown" and r["change_pct"] is None


def test_e5_change_pct_rounded():
    rows = compare_to_baseline({"decode_tps": 30.0}, {"decode_tps": 31.0}, {"decode_tps": 5})
    assert rows[0]["change_pct"] == 3.3


def test_e6_lower_better():
    assert status("load_seconds", 11.5, 10) == "failed"
    assert status("load_seconds", 11.0, 10) == "passed"
    assert status("load_seconds", 2.0, 10) == "passed"


def test_e7_higher_better():
    assert status("decode_tps", 35.0, 10) == "failed"
    assert status("decode_tps", 36.0, 10) == "passed"
    assert status("decode_tps", 80.0, 10) == "passed"


def test_e8_inputs_unchanged():
    b, cnd, t = copy.deepcopy(BASE), {"decode_tps": 41.0}, {"decode_tps": 5}
    compare_to_baseline(b, cnd, t)
    assert b == BASE and cnd == {"decode_tps": 41.0} and t == {"decode_tps": 5}
