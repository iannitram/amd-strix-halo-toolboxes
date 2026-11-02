"""Recipe schema version 1 and its validation (R1). Planned: #17.

Shape (SPEC.md, Shared data contracts, Recipe):
    schema_version, id, name, created_at, updated_at, provenance{source,...},
    image{repository, digest, tag?}, engine{name, revision}, backend, platform,
    model{repo?, revision?, files[{name, sha256, size_bytes}]}, sidecars?[same as files],
    launch{ctx_size, parallel?, flash_attn?, no_mmap?, extra?}, constraints?, qualification?
"""

import re

SCHEMA_VERSION = 1
SUPPORTED_VERSIONS = (1,)
REQUIRED_FIELDS = (
    "schema_version", "id", "name", "created_at", "updated_at", "provenance.source",
    "image.repository", "image.digest", "engine.name", "engine.revision",
    "backend", "platform", "model.files", "launch.ctx_size",
)


def validate_recipe(recipe) -> list:
    """Return every problem with ``recipe`` as strings, in a fixed order; [] when valid."""
    if not isinstance(recipe, dict):
        return ["recipe must be an object"]

    version = recipe.get("schema_version")
    if "schema_version" in recipe and version not in SUPPORTED_VERSIONS:
        return [f"unsupported schema_version: {version}"]

    errors = []
    for path in REQUIRED_FIELDS:
        value = recipe
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]
        if value is None or value == "":
            errors.append(f"missing field: {path}")

    image = recipe.get("image")
    if isinstance(image, dict):
        digest = image.get("digest")
        if digest not in (None, "") and (
            not isinstance(digest, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
        ):
            errors.append("image.digest must look like sha256:<64 hex>")

    def check_file_items(files, prefix):
        for index, item in enumerate(files):
            item_prefix = f"{prefix}[{index}]"
            fields = item if isinstance(item, dict) else {}
            if not fields.get("name"):
                errors.append(f"{item_prefix}.name missing")
            sha256 = fields.get("sha256")
            if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
                errors.append(f"{item_prefix}.sha256 must be 64 hex")
            size = fields.get("size_bytes")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                errors.append(f"{item_prefix}.size_bytes must be a non-negative integer")

    model = recipe.get("model")
    model_files = model.get("files") if isinstance(model, dict) else None
    if model_files is not None and model_files != "":
        if not isinstance(model_files, list) or not model_files:
            errors.append("model.files must not be empty")
        else:
            check_file_items(model_files, "model.files")

    if "sidecars" in recipe:
        sidecars = recipe["sidecars"]
        if not isinstance(sidecars, list):
            errors.append("sidecars must be a list")
        else:
            check_file_items(sidecars, "sidecars")

    launch = recipe.get("launch")
    if isinstance(launch, dict):
        for field in ("ctx_size", "parallel"):
            if field not in launch:
                continue
            value = launch[field]
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"launch.{field} must be a positive integer")

    identifier = recipe.get("id")
    if identifier is not None and (
        not isinstance(identifier, str)
        or re.fullmatch(r"rcp-[0-9a-f]{16}", identifier) is None
    ):
        errors.append("id must look like rcp-<16 hex>")

    return errors
