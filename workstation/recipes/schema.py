"""Recipe schema version 1 and its validation (R1). Planned: #17.

Shape (SPEC.md, Shared data contracts, Recipe):
    schema_version, id, name, created_at, updated_at, provenance{source,...},
    image{repository, digest, tag?}, engine{name, revision}, backend, platform,
    model{repo?, revision?, files[{name, sha256, size_bytes}]}, sidecars?[same as files],
    launch{ctx_size, parallel?, flash_attn?, no_mmap?, extra?}, constraints?, qualification?
"""

SCHEMA_VERSION = 1
SUPPORTED_VERSIONS = (1,)
REQUIRED_FIELDS = (
    "schema_version", "id", "name", "created_at", "updated_at", "provenance.source",
    "image.repository", "image.digest", "engine.name", "engine.revision",
    "backend", "platform", "model.files", "launch.ctx_size",
)


def validate_recipe(recipe) -> list:
    """Return every problem with ``recipe`` as strings, in a fixed order; [] when valid."""
    raise NotImplementedError("TODO #17")
