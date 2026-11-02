"""Locked tests for #17 (workstation/recipes/schema.py). One test per Expectation sentence."""

import copy

from workstation.recipes.schema import validate_recipe

FILE = {"name": "m-00001-of-00001.gguf", "sha256": "b" * 64, "size_bytes": 1024}
VALID = {
    "schema_version": 1,
    "id": "rcp-0123456789abcdef",
    "name": "coder",
    "created_at": "2026-11-02T10:00:00Z",
    "updated_at": "2026-11-02T10:00:00Z",
    "provenance": {"source": "test"},
    "image": {"repository": "docker.io/kyuz0/amd-strix-halo-toolboxes",
              "digest": "sha256:" + "a" * 64},
    "engine": {"name": "llama.cpp", "revision": "b7000"},
    "backend": "vulkan-radv",
    "platform": "gfx1151",
    "model": {"files": [FILE]},
    "launch": {"ctx_size": 8192},
}


def v(**changes):
    r = copy.deepcopy(VALID)
    r.update(changes)
    return r


def test_e1_valid_recipe_has_no_errors_and_is_unchanged():
    data = copy.deepcopy(VALID)
    assert validate_recipe(data) == []
    assert data == VALID


def test_e2_not_a_dict():
    assert validate_recipe([1]) == ["recipe must be an object"]
    assert validate_recipe(None) == ["recipe must be an object"]


def test_e3_unsupported_schema_version_is_the_only_error():
    assert validate_recipe({"schema_version": 3}) == ["unsupported schema_version: 3"]


def test_e4_missing_fields_in_required_order():
    errors = validate_recipe({"schema_version": 1, "image": {"digest": ""}, "model": None})
    assert errors == [
        "missing field: id", "missing field: name", "missing field: created_at",
        "missing field: updated_at", "missing field: provenance.source",
        "missing field: image.repository", "missing field: image.digest",
        "missing field: engine.name", "missing field: engine.revision",
        "missing field: backend", "missing field: platform", "missing field: model.files",
        "missing field: launch.ctx_size",
    ]
    assert validate_recipe({})[0] == "missing field: schema_version"


def test_e5_digest_format():
    r = v(image={"repository": "x", "digest": "sha256:" + "A" * 64})
    assert validate_recipe(r) == ["image.digest must look like sha256:<64 hex>"]


def test_e6_model_files_items():
    assert validate_recipe(v(model={"files": []})) == ["model.files must not be empty"]
    bad = {"name": "", "sha256": "xyz", "size_bytes": True}
    assert validate_recipe(v(model={"files": [FILE, bad]})) == [
        "model.files[1].name missing",
        "model.files[1].sha256 must be 64 hex",
        "model.files[1].size_bytes must be a non-negative integer",
    ]
    assert validate_recipe(v(model={"files": [{"name": "a", "sha256": "c" * 64,
                                               "size_bytes": -1}]})) == [
        "model.files[0].size_bytes must be a non-negative integer"]


def test_e7_sidecars_optional_but_checked():
    assert validate_recipe(v(sidecars=[FILE])) == []
    assert validate_recipe(v(sidecars="x")) == ["sidecars must be a list"]
    assert validate_recipe(v(sidecars=[{"name": "s", "sha256": "d" * 64}])) == [
        "sidecars[0].size_bytes must be a non-negative integer"]


def test_e8_launch_numbers():
    assert validate_recipe(v(launch={"ctx_size": 0})) == [
        "launch.ctx_size must be a positive integer"]
    assert validate_recipe(v(launch={"ctx_size": True})) == [
        "launch.ctx_size must be a positive integer"]
    assert validate_recipe(v(launch={"ctx_size": 4096, "parallel": 0})) == [
        "launch.parallel must be a positive integer"]
    assert validate_recipe(v(launch={"ctx_size": 4096, "parallel": 2})) == []


def test_e9_id_format():
    assert validate_recipe(v(id="rcp-XYZ")) == ["id must look like rcp-<16 hex>"]
