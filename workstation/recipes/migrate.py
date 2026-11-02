"""Recipe schema migrations (R1). Planned: #1.

MIGRATIONS maps a schema version to a function that returns the recipe at the next version.
"""

MIGRATIONS = {}


def migrate(recipe) -> dict:
    """Return ``recipe`` at the current SCHEMA_VERSION; raise RecipeError when there is no path."""
    raise NotImplementedError("TODO #1")
