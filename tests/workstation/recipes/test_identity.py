"""Locked tests for #16 (workstation/recipes/identity.py). One test per Expectation sentence."""

import copy
import hashlib
import json

import pytest

from workstation.recipes.identity import canonical_json, recipe_id

RECIPE = {
    "schema_version": 1,
    "id": "rcp-0000000000000000",
    "name": "coder",
    "created_at": "2026-11-02T10:00:00Z",
    "updated_at": "2026-11-02T10:00:00Z",
    "provenance": {"source": "test"},
    "qualification": None,
    "image": {"repository": "docker.io/kyuz0/amd-strix-halo-toolboxes",
              "digest": "sha256:" + "a" * 64, "tag": "vulkan-radv"},
    "backend": "vulkan-radv",
    "launch": {"ctx_size": 8192},
}


def test_e1_canonical_json_format():
    obj = {"b": [1, 2], "a": {"é": "ü", "c": None}}
    assert canonical_json(obj) == '{"a":{"c":null,"é":"ü"},"b":[1,2]}'


def test_e2_canonical_json_rejects_nan_and_infinity():
    with pytest.raises(ValueError):
        canonical_json({"x": float("nan")})
    with pytest.raises(ValueError):
        canonical_json({"x": float("inf")})


def test_e3_volatile_keys_and_tag_left_out_input_unchanged():
    data = copy.deepcopy(RECIPE)
    before = copy.deepcopy(data)
    recipe_id(data)
    assert data == before


def test_e4_hash_of_the_rest():
    rest = {"schema_version": 1,
            "image": {"repository": "docker.io/kyuz0/amd-strix-halo-toolboxes",
                      "digest": "sha256:" + "a" * 64},
            "backend": "vulkan-radv", "launch": {"ctx_size": 8192}}
    text = json.dumps(rest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    expected = "rcp-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    assert recipe_id(RECIPE) == expected
    assert len(expected) == 20


def test_e5_same_id_for_volatile_changes_new_id_otherwise():
    other = copy.deepcopy(RECIPE)
    other.update(id="rcp-1111111111111111", name="renamed", created_at="x", updated_at="y",
                 provenance={"source": "elsewhere"}, qualification="qual-1")
    other["image"]["tag"] = "latest"
    assert recipe_id(other) == recipe_id(RECIPE)
    changed = copy.deepcopy(RECIPE)
    changed["launch"]["ctx_size"] = 4096
    assert recipe_id(changed) != recipe_id(RECIPE)
    no_tag = copy.deepcopy(RECIPE)
    del no_tag["image"]["tag"]
    assert recipe_id(no_tag) == recipe_id(RECIPE)
