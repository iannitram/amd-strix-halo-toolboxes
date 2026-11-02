"""On-disk recipe store: save, list, load, by ID and by name (R1). Planned: #1.

Files: <root>/recipes/<id>.json, written atomically (temp file + rename).
"""


class RecipeStore:
    def __init__(self, root):
        self.root = root

    def save(self, recipe) -> str:
        raise NotImplementedError("TODO #1")

    def load(self, recipe_id: str) -> dict:
        raise NotImplementedError("TODO #1")

    def load_by_name(self, name: str) -> dict:
        raise NotImplementedError("TODO #1")

    def list(self) -> list:
        raise NotImplementedError("TODO #1")
