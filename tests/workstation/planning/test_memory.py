"""Locked tests for #27 (workstation/planning/memory.py). One test per Expectation sentence."""

import pytest

from workstation.planning.memory import kv_cache_bytes, memory_plan

LLAMA = dict(n_layers=32, n_head_kv=8, key_length=128, value_length=128, ctx=8192)


def test_e1_full_attention_by_cache_type():
    assert kv_cache_bytes(**LLAMA) == 1_073_741_824
    assert kv_cache_bytes(**LLAMA, cache_type="bf16") == 1_073_741_824
    assert kv_cache_bytes(**LLAMA, cache_type="q8_0") == 570_425_344
    assert kv_cache_bytes(**LLAMA, cache_type="q4_0") == 301_989_888


def test_e2_sliding_window_layers():
    got = kv_cache_bytes(n_layers=48, n_head_kv=8, key_length=128, value_length=128,
                         ctx=32768, swa_layers=40, swa_window=1024)
    assert got == 1_241_513_984
    small = kv_cache_bytes(n_layers=4, n_head_kv=1, key_length=1, value_length=1, ctx=10,
                           swa_layers=4, swa_window=100)
    assert small == 4 * 10 * 2 * 2


def test_e3_rounds_up():
    assert kv_cache_bytes(n_layers=1, n_head_kv=1, key_length=1, value_length=0, ctx=1,
                          cache_type="q4_0") == 1


def test_e4_errors():
    with pytest.raises(ValueError, match="^unknown cache type: q2$"):
        kv_cache_bytes(**LLAMA, cache_type="q2")
    with pytest.raises(ValueError, match="^sizes must be >= 0$"):
        kv_cache_bytes(**{**LLAMA, "ctx": -1})
    with pytest.raises(ValueError, match="^swa_layers must be <= n_layers$"):
        kv_cache_bytes(**LLAMA, swa_layers=33, swa_window=10)


def test_e5_plan_fits():
    p = memory_plan(weights_bytes=60, kv_bytes=10, runtime_reserve_bytes=5,
                    desktop_reserve_bytes=15, total_bytes=100)
    assert p == {"parts": {"weights": 60, "kv_cache": 10, "runtime_reserve": 5,
                           "desktop_reserve": 15},
                 "required": 90, "total": 100, "headroom": 10, "fits": True, "status": "fits"}
    exact = memory_plan(weights_bytes=100, kv_bytes=0, runtime_reserve_bytes=0,
                        desktop_reserve_bytes=0, total_bytes=100)
    assert exact["fits"] is True and exact["headroom"] == 0


def test_e6_plan_does_not_fit():
    p = memory_plan(weights_bytes=90, kv_bytes=20, runtime_reserve_bytes=0,
                    desktop_reserve_bytes=0, total_bytes=100)
    assert p["fits"] is False and p["status"] == "does-not-fit" and p["headroom"] == -10


def test_e7_plan_unknown_total():
    p = memory_plan(weights_bytes=1, kv_bytes=1, runtime_reserve_bytes=1,
                    desktop_reserve_bytes=1, total_bytes=None)
    assert p["required"] == 4 and p["status"] == "unknown"
    assert p["total"] is None and p["headroom"] is None and p["fits"] is None


def test_e8_plan_negative_sizes():
    with pytest.raises(ValueError, match="^sizes must be >= 0$"):
        memory_plan(weights_bytes=-1, kv_bytes=0, runtime_reserve_bytes=0,
                    desktop_reserve_bytes=0, total_bytes=10)
