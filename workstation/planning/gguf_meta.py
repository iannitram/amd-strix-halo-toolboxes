"""Structured GGUF metadata from local files, over the existing estimator (P1). Planned: #30.

Wraps toolboxes/gguf-vram-estimator.py (loaded with importlib: its name has hyphens);
that script's CLI stays exactly as it is.
"""


def read_local(path) -> dict:
    raise NotImplementedError("TODO #30")
