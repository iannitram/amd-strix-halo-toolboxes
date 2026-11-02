"""Locked tests for #18 (workstation/recipes/io.py). One test per Expectation sentence."""

import copy
import json

import pytest

from workstation.errors import RecipeError
from workstation.recipes.identity import recipe_id
from workstation.recipes.io import export_recipe, import_recipe

FILE = {"name": "m.gguf", "sha256": "b" * 64, "size_bytes": 1024}
VALID = {
    "schema_version": 1,
    "id": "rcp-0123456789abcdef",
    "name": "coder",
    "created_at": "2026-11-02T10:00:00Z",
    "updated_at": "2026-11-02T10:00:00Z",
    "provenance": {"source": "test", "token": "hf_secret"},
    "image": {"repository": "docker.io/kyuz0/amd-strix-halo-toolboxes",
              "digest": "sha256:" + "a" * 64, "tag": "vulkan-radv"},
    "engine": {"name": "llama.cpp", "revision": "b7000"},
    "backend": "vulkan-radv",
    "platform": "gfx1151",
    "model": {"files": [FILE]},
    "launch": {"ctx_size": 8192, "extra": ["--model", "/home/alice/m.gguf"]},
}


def test_e1_invalid_recipe_raises_with_all_errors():
    bad = copy.deepcopy(VALID)
    del bad["backend"]
    bad["launch"]["ctx_size"] = 0
    with pytest.raises(RecipeError) as info:
        export_recipe(bad)
    assert info.value.errors == ["missing field: backend",
                                 "launch.ctx_size must be a positive integer"]


def test_e2_redacted_and_reidentified():
    out = json.loads(export_recipe(VALID))
    assert out["provenance"] == {"source": "test", "token": "[redacted]"}
    assert out["launch"]["extra"] == ["--model", "~/m.gguf"]
    assert out["id"] == recipe_id(out)
    assert out["id"] != VALID["id"]


def test_e3_fixed_text_and_input_unchanged():
    data = copy.deepcopy(VALID)
    text = export_recipe(data, home_dirs=("/data/me",))
    assert data == VALID
    expected = json.loads(text)
    assert text == json.dumps(expected, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert text.endswith("}\n")


def test_e4_not_json():
    with pytest.raises(RecipeError) as info:
        import_recipe("{nope")
    assert len(info.value.errors) == 1
    assert info.value.errors[0].startswith("not valid JSON: ")


def test_e5_invalid_recipe_text():
    with pytest.raises(RecipeError) as info:
        import_recipe(json.dumps({"schema_version": 9}))
    assert info.value.errors == ["unsupported schema_version: 9"]


def test_e6_wrong_id():
    good = json.loads(export_recipe(VALID))
    tampered = dict(good, backend="rocm-7.2.4")
    with pytest.raises(RecipeError) as info:
        import_recipe(json.dumps(tampered))
    assert info.value.errors == [
        f"id does not match contents: expected {recipe_id(tampered)}"]


def test_e7_round_trip():
    text = export_recipe(VALID)
    back = import_recipe(text)
    assert isinstance(back, dict)
    assert export_recipe(back) == text
