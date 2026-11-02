"""Locked tests for #28 (workstation/planning/disk.py). One test per Expectation sentence."""

import copy

import pytest

from workstation.planning.disk import check_shards, plan_disk


def test_e1_single_file_and_complete_set():
    assert check_shards(["model.gguf"]) == {"complete": True, "missing": [], "groups": []}
    names = ["m-00001-of-00002.gguf", "m-00002-of-00002.gguf"]
    assert check_shards(names) == {"complete": True, "missing": [], "groups": ["m"]}


def test_e2_missing_shards_sorted():
    out = check_shards(["b-00002-of-00003.gguf", "a-00001-of-00002.gguf"])
    assert out["complete"] is False
    assert out["missing"] == ["a-00002-of-00002.gguf", "b-00001-of-00003.gguf",
                              "b-00003-of-00003.gguf"]
    assert out["groups"] == ["a", "b"]


def test_e3_names_unchanged():
    names = ["m-00001-of-00002.gguf"]
    check_shards(names)
    assert names == ["m-00001-of-00002.gguf"]


def test_e4_plan_counts_download_and_reuse():
    files = [{"name": "a", "size": 100, "present": True}, {"name": "b", "size": 50},
             {"name": "c", "size": 30, "present": False}]
    before = copy.deepcopy(files)
    p = plan_disk(files, temp_factor=0.5, cache_bytes=7, free_bytes=200)
    assert files == before
    assert p == {"download_bytes": 80, "reusable_bytes": 100, "temp_bytes": 40,
                 "cache_bytes": 7, "required_bytes": 127, "free_bytes": 200,
                 "fits": True, "status": "fits"}


def test_e5_temp_rounds_up():
    assert plan_disk([{"name": "a", "size": 3}], temp_factor=0.5)["temp_bytes"] == 2


def test_e6_fit_status():
    files = [{"name": "a", "size": 100}]
    assert plan_disk(files, free_bytes=100)["status"] == "fits"
    p = plan_disk(files, free_bytes=99)
    assert p["fits"] is False and p["status"] == "does-not-fit"
    p = plan_disk(files)
    assert p["fits"] is None and p["status"] == "unknown" and p["free_bytes"] is None


def test_e7_negative_sizes():
    with pytest.raises(ValueError, match="^sizes must be >= 0$"):
        plan_disk([{"name": "a", "size": -1}])
    with pytest.raises(ValueError, match="^sizes must be >= 0$"):
        plan_disk([], cache_bytes=-1)
