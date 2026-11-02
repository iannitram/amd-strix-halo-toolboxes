"""Hand-worked model/host fixtures for the explained planner (#4)."""

from copy import deepcopy

import pytest

from workstation.planning.gguf_meta import read_local
from workstation.planning.planner import alternatives, plan

GIB = 1024**3
NOW = "2026-11-02T12:00:00Z"


@pytest.fixture
def dense():
    return {
        "architecture": "llama", "n_layers": 32, "n_head_kv": 8,
        "key_length": 128, "value_length": 128,
        "sliding_window_layers": 0, "sliding_window_size": None,
        "full_attention_layers": 32, "total_size_bytes": 4 * GIB,
        "files": [{"name": "model.gguf", "size": 4 * GIB}],
    }


@pytest.fixture
def choices():
    return {
        "ctx_size": 8192, "cache_type": "f16", "parallel": 2,
        "runtime_reserve_bytes": GIB, "desktop_reserve_bytes": 2 * GIB,
        "temp_factor": 0.5, "cache_bytes": GIB, "now": NOW,
    }


@pytest.fixture
def host():
    return {
        "sampled_at": NOW, "memory": {"total_bytes": 16 * GIB, "free_bytes": 10 * GIB},
        "disk_free_bytes": 12 * GIB,
    }


def test_dense_model_has_hand_worked_memory_disk_and_labels(dense, choices, host):
    result = plan(dense, choices, host)
    memory, disk = result["memory"], result["disk"]
    # 32 layers * 8 KV heads * (128 + 128) * 8192 tokens * 2 bytes * 2 users.
    assert {key: value["value"] for key, value in memory["parts"].items()} == {
        "weights": 4 * GIB, "kv_cache": 2 * GIB,
        "runtime_reserve": GIB, "desktop_reserve": 2 * GIB,
    }
    assert memory["required"]["value"] == 9 * GIB
    assert memory["total"]["value"] == 16 * GIB  # Shared CPU/GPU capacity counted once.
    assert memory["headroom"]["value"] == 7 * GIB
    assert {key: value["value"] for key, value in disk.items() if isinstance(value, dict)} == {
        "download_bytes": 4 * GIB, "reusable_bytes": 0, "temp_bytes": 2 * GIB,
        "cache_bytes": GIB, "required_bytes": 7 * GIB, "free_bytes": 12 * GIB,
    }
    assert result["fits"] is True and result["status"] == "fits"
    assert memory["total"]["label"] == disk["free_bytes"]["label"] == "measured"
    assert memory["parts"]["weights"]["label"] == "estimated"
    assert memory["parts"]["kv_cache"]["label"] == "estimated"
    assert disk["temp_bytes"]["label"] == "estimated"
    assert result["uncertainties"]  # An estimate is not evidence of real GPU behaviour.


def test_all_resource_numbers_and_numeric_assumptions_are_labelled(dense, choices, host):
    result = plan(dense, choices, host)

    def check(value):
        if isinstance(value, dict) and "label" in value:
            assert set(value) == {"value", "label", "source", "age_s"}
            assert value["label"] in {"estimated", "measured", "stale", "unknown"}
        elif isinstance(value, dict):
            for child in value.values():
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)
        else:
            assert value is None or isinstance(value, (str, bool))

    check(result)


def test_sliding_window_caps_each_users_cache(dense, choices, host):
    dense.update(n_layers=48, sliding_window_layers=40, sliding_window_size=1024,
                 full_attention_layers=8)
    choices["ctx_size"] = 32768
    result = plan(dense, choices, host)
    # (8 * 32768 + 40 * 1024) * 8 * (128 + 128) * 2 * 2 users.
    assert result["memory"]["parts"]["kv_cache"]["value"] == 2_483_027_968
    choices["ctx_size"] = 512
    assert plan(dense, choices, host)["memory"]["parts"]["kv_cache"]["value"] == 201_326_592


def test_missing_split_shard_invalidates_partial_totals(dense, choices, host):
    dense.pop("files")
    dense.update(file_sizes_bytes={"model-00001-of-00002.gguf": GIB}, total_size_bytes=GIB)
    result = plan(dense, choices, host)
    assert result["shards"] == {
        "complete": False, "missing": ["model-00002-of-00002.gguf"], "groups": ["model"],
    }
    for number in (result["memory"]["parts"]["weights"], result["memory"]["required"],
                   result["memory"]["headroom"], result["disk"]["download_bytes"],
                   result["disk"]["temp_bytes"], result["disk"]["required_bytes"]):
        assert number["value"] is None and number["label"] == "unknown"
    assert result["disk"]["reusable_bytes"]["value"] == GIB
    assert result["fits"] is not True
    assert any("Missing model shards" in item for item in result["uncertainties"])


@pytest.mark.parametrize("field", [
    "architecture", "n_layers", "n_head_kv", "key_length", "value_length",
    "sliding_window_layers",
])
def test_missing_kv_metadata_is_unknown_never_green(dense, choices, host, field):
    dense.pop(field)
    result = plan(dense, choices, host)
    assert result["memory"]["parts"]["kv_cache"]["label"] == "unknown"
    assert result["memory"]["required"]["value"] is None
    assert result["memory"]["headroom"]["value"] is None
    assert result["memory"]["parts"]["weights"]["value"] == 4 * GIB
    assert result["disk"]["required_bytes"]["value"] == 7 * GIB
    assert result["fits"] is None and result["status"] == "unknown"
    assert any(field in item for item in result["uncertainties"])


def test_missing_window_does_not_treat_sliding_layers_as_zero(dense, choices, host):
    dense["sliding_window_layers"] = 20
    assert plan(dense, choices, host)["memory"]["parts"]["kv_cache"]["label"] == "unknown"


def test_empty_inputs_return_unknowns():
    result = plan({}, {}, {})
    assert result["fits"] is None and result["status"] == "unknown"
    assert result["shards"]["complete"] is None
    assert result["memory"]["parts"]["weights"]["label"] == "unknown"
    assert result["disk"]["required_bytes"]["label"] == "unknown"


def test_missing_file_size_preserves_known_reusable_bytes(dense, choices, host):
    dense.pop("total_size_bytes")
    dense["files"] = [
        {"name": "model-00001-of-00002.gguf", "size": GIB, "present": True},
        {"name": "model-00002-of-00002.gguf", "size": None},
    ]
    result = plan(dense, choices, host)
    assert result["shards"]["complete"] is True
    assert result["memory"]["parts"]["weights"]["label"] == "unknown"
    assert result["disk"]["download_bytes"]["label"] == "unknown"
    assert result["disk"]["reusable_bytes"]["value"] == GIB
    assert result["fits"] is None


def test_complete_split_manifest_sums_weights_and_only_downloads_missing_files(
    dense, choices, host,
):
    dense.pop("total_size_bytes")
    dense["files"] = [
        {"name": "model-00001-of-00002.gguf", "size": 3 * GIB, "present": True},
        {"name": "model-00002-of-00002.gguf", "size": GIB},
    ]
    result = plan(dense, choices, host)
    assert result["memory"]["parts"]["weights"]["value"] == 4 * GIB
    assert result["disk"]["download_bytes"]["value"] == GIB
    assert result["disk"]["reusable_bytes"]["value"] == 3 * GIB
    assert result["disk"]["required_bytes"]["value"] == 5 * GIB // 2
    assert result["fits"] is True


def test_plans_actual_local_reader_output(tmp_path, choices, host):
    import struct

    def string(text):
        data = text.encode("utf-8")
        return struct.pack("<Q", len(data)) + data

    metadata = string("general.architecture") + struct.pack("<I", 8) + string("llama")
    for key, value in [("block_count", 32), ("attention.head_count_kv", 8),
                       ("attention.key_length", 128), ("attention.value_length", 128)]:
        metadata += string("llama." + key) + struct.pack("<II", 4, value)
    model = tmp_path / "model.gguf"
    model.write_bytes(struct.pack("<IIQQ", 0x46554747, 3, 0, 5) + metadata)
    result = plan(read_local(model), choices, host)
    assert result["memory"]["parts"]["weights"]["value"] == model.stat().st_size
    assert result["memory"]["parts"]["kv_cache"]["value"] == 2 * GIB
    assert result["disk"]["download_bytes"]["value"] == 0
    assert result["disk"]["reusable_bytes"]["label"] == "stale"


@pytest.mark.parametrize("section", ["memory", "disk"])
def test_insufficient_capacity_is_explained(dense, choices, host, section):
    if section == "memory":
        host["memory"]["total_bytes"] = 8 * GIB
    else:
        host["disk_free_bytes"] = 6 * GIB
    result = plan(dense, choices, host)
    assert result[section]["fits"] is False
    assert result["fits"] is False and result["status"] == "does-not-fit"
    if section == "memory":
        assert result[section]["headroom"]["value"] == -GIB


def test_missing_host_and_reserves_never_claim_fit(dense, choices):
    choices.pop("runtime_reserve_bytes")
    result = plan(dense, choices, {})
    assert result["memory"]["parts"]["runtime_reserve"]["label"] == "unknown"
    assert result["memory"]["total"]["label"] == "unknown"
    assert result["disk"]["free_bytes"]["label"] == "unknown"
    assert result["fits"] is None


@pytest.mark.parametrize("now", [None, "2026-11-02T12:05:01Z"])
def test_measurements_without_fresh_times_are_stale(dense, choices, host, now):
    choices["now"] = now
    result = plan(dense, choices, host)
    assert result["memory"]["total"]["label"] == "stale"
    assert result["disk"]["free_bytes"]["label"] == "stale"
    assert "memory.total: stale" in result["uncertainties"]


def test_supported_alternatives_have_recomputed_plans_and_do_not_mutate(dense, choices, host):
    backend = {"supported_choices": [
        {"ctx_size": 4096, "cache_type": "f16", "parallel": 2},
        {"ctx_size": 8192, "cache_type": "q8_0", "parallel": 2},
        {"ctx_size": 8192, "cache_type": "f16", "parallel": 1},
    ]}
    before = deepcopy((dense, choices, host, backend))
    result = alternatives(dense, choices, host, backend=backend)
    assert [item["changes"] for item in result] == [
        {"ctx_size": 4096}, {"cache_type": "q8_0"}, {"parallel": 1},
    ]
    assert [item["plan"]["memory"]["parts"]["kv_cache"]["value"] for item in result] == [
        GIB, 1_140_850_688, GIB,
    ]
    for item in result:
        candidate = {**choices, **item["changes"]}
        assert {key: candidate[key] for key in ("ctx_size", "cache_type", "parallel")} in (
            backend["supported_choices"]
        )
        assert item["plan"] == plan(dense, candidate, host)
    assert (dense, choices, host, backend) == before


def test_alternatives_reject_unsupported_combinations_and_are_deterministic(dense, choices, host):
    entries = [
        {"ctx_size": 8192, "cache_type": "q4_0", "parallel": 2},
        {"ctx_size": 8192, "cache_type": "q8_0", "parallel": 2},
        {"ctx_size": 8192, "cache_type": "q8_0", "parallel": 2},
        {"ctx_size": 4096, "cache_type": "q4_0", "parallel": 1},  # Coupled constraints.
        {"ctx_size": 8192, "cache_type": "q2", "parallel": 2},
        {"ctx_size": 16384, "cache_type": "f16", "parallel": 2},
        {"ctx_size": 8192, "cache_type": "bf16", "parallel": 2},  # Equal cache size.
        {"ctx_size": 8192, "cache_type": "f16", "parallel": 0},
    ]
    result = alternatives(dense, choices, host, backend={"supported_choices": entries})
    assert [item["changes"] for item in result] == [{"cache_type": "q8_0"}, {"cache_type": "q4_0"}]
    reversed_result = alternatives(
        dense, choices, host, backend={"supported_choices": entries[::-1]},
    )
    assert reversed_result == result
    assert alternatives(dense, choices, host, backend={}) == []


def test_alternatives_with_missing_metadata_remain_unknown(dense, choices, host):
    dense.pop("n_head_kv")
    backend = {"supported_choices": [{"ctx_size": 4096, "cache_type": "f16", "parallel": 2}]}
    result = alternatives(dense, choices, host, backend=backend)
    assert len(result) == 1
    assert result[0]["plan"]["fits"] is None
    assert result[0]["plan"]["memory"]["parts"]["kv_cache"]["label"] == "unknown"


def test_missing_reusable_size_never_claims_fit_even_with_known_weights(dense, choices, host):
    dense["files"] = [{"name": "model.gguf", "size": None, "present": True}]
    result = plan(dense, choices, host)
    assert result["memory"]["parts"]["weights"]["value"] == 4 * GIB
    assert result["disk"]["reusable_bytes"]["label"] == "unknown"
    assert result["fits"] is None and result["status"] == "unknown"


def test_incomplete_backend_declarations_are_not_supported(dense, choices, host):
    choices.pop("parallel")
    backend = {"supported_choices": [{"ctx_size": 4096, "cache_type": "f16"}]}
    assert alternatives(dense, choices, host, backend=backend) == []


def test_explicit_zero_reserves_and_default_disk_policy_are_valid(dense, choices, host):
    choices.update(runtime_reserve_bytes=0, desktop_reserve_bytes=0)
    choices.pop("temp_factor")
    choices.pop("cache_bytes")
    result = plan(dense, choices, host)
    assert result["memory"]["required"]["value"] == 6 * GIB
    assert result["disk"]["temp_bytes"]["value"] == 0
    assert result["disk"]["cache_bytes"]["value"] == 0
    assert result["fits"] is True


@pytest.mark.parametrize("setting,value", [
    ("ctx_size", 0), ("parallel", -1), ("cache_type", "q2"),
    ("runtime_reserve_bytes", -1), ("temp_factor", float("inf")), ("cache_bytes", -1),
])
def test_invalid_choices_are_rejected(dense, choices, host, setting, value):
    choices[setting] = value
    with pytest.raises(ValueError):
        plan(dense, choices, host)
