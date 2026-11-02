"""Deterministic, redacted recipe export and checked import (R1)."""

import json

from workstation.errors import RecipeError
from workstation.recipes.identity import recipe_id
from workstation.recipes.schema import validate_recipe
from workstation.redact import redact


def export_recipe(recipe, *, home_dirs=()) -> str:
    """Validate, redact, re-identify; return fixed JSON text ending in a newline."""
    errors = validate_recipe(recipe)
    if errors:
        raise RecipeError(errors)

    result = redact(recipe, home_dirs=home_dirs)
    result["id"] = recipe_id(result)
    return json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def import_recipe(text: str) -> dict:
    """Parse and check exported recipe text; raise RecipeError listing every problem."""
    try:
        recipe = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RecipeError([f"not valid JSON: {exc.msg}"]) from exc

    errors = validate_recipe(recipe)
    if errors:
        raise RecipeError(errors)

    expected_id = recipe_id(recipe)
    if recipe["id"] != expected_id:
        raise RecipeError([f"id does not match contents: expected {expected_id}"])
    return recipe
