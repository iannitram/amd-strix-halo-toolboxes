"""Deterministic, redacted recipe export and checked import (R1). Planned: #18."""


def export_recipe(recipe, *, home_dirs=()) -> str:
    """Validate, redact, re-identify; return fixed JSON text ending in a newline."""
    raise NotImplementedError("TODO #18")


def import_recipe(text: str) -> dict:
    """Parse and check exported recipe text; raise RecipeError listing every problem."""
    raise NotImplementedError("TODO #18")
