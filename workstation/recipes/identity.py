"""Deterministic recipe identity (R1). Planned: #16."""

import hashlib
import json

ID_PREFIX = "rcp-"
# Top-level keys that do not change what a recipe runs, so they are left out of its ID.
VOLATILE_KEYS = ("id", "name", "created_at", "updated_at", "provenance", "qualification")


def canonical_json(obj) -> str:
    """One fixed JSON text for ``obj``: sorted keys, no spaces, UTF-8 kept, no NaN."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def recipe_id(recipe) -> str:
    """``rcp-`` plus the first 16 hex digits of the SHA-256 of the recipe's canonical JSON."""
    stable_recipe = {key: value for key, value in recipe.items() if key not in VOLATILE_KEYS}
    image = stable_recipe.get("image")
    if isinstance(image, dict):
        stable_recipe["image"] = {key: value for key, value in image.items() if key != "tag"}

    digest = hashlib.sha256(canonical_json(stable_recipe).encode("utf-8")).hexdigest()
    return ID_PREFIX + digest[:16]
