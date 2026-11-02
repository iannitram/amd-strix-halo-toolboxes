"""Deterministic recipe identity (R1). Planned: #16."""

ID_PREFIX = "rcp-"
# Top-level keys that do not change what a recipe runs, so they are left out of its ID.
VOLATILE_KEYS = ("id", "name", "created_at", "updated_at", "provenance", "qualification")


def canonical_json(obj) -> str:
    """One fixed JSON text for ``obj``: sorted keys, no spaces, UTF-8 kept, no NaN."""
    raise NotImplementedError("TODO #16")


def recipe_id(recipe) -> str:
    """``rcp-`` plus the first 16 hex digits of the SHA-256 of the recipe's canonical JSON."""
    raise NotImplementedError("TODO #16")
