"""Structured GGUF metadata from local files, reusing the existing estimator."""

import importlib.util
import os
import re
import struct
from pathlib import Path


_ESTIMATOR_PATH = Path(__file__).resolve().parents[2] / "toolboxes" / "gguf-vram-estimator.py"
_SPLIT_NAME = re.compile(r"-(\d{5})-of-(\d{5})\.gguf$", re.IGNORECASE)


def _estimator():
    spec = importlib.util.spec_from_file_location("gguf_vram_estimator", _ESTIMATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load GGUF estimator at {_ESTIMATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bounded_reader(estimator):
    """The estimator's reader, except a string longer than the rest of the file is an error.

    Without this check a malformed length header asks for a huge allocation before any read fails.
    """

    class BoundedReader(estimator.GGUFMetadataReader):
        def _read_string(self) -> str:
            header = self.f.read(8)
            if len(header) != 8:
                raise ValueError("truncated GGUF string header")
            (length,) = struct.unpack("<Q", header)
            remaining = os.fstat(self.f.fileno()).st_size - self.f.tell()
            if length > remaining:
                raise ValueError("GGUF string runs past the end of the file")
            return self.f.read(length).decode("utf-8", errors="replace")

        def _skip_value(self, value_type_idx: int):
            # The estimator ignores 64-bit types and silently misreads past unknown ones.
            if value_type_idx in (10, 11, 12):
                self.f.seek(8, 1)
            elif value_type_idx not in range(10):
                raise ValueError(f"unknown GGUF value type {value_type_idx}")
            else:
                super()._skip_value(value_type_idx)

    return BoundedReader


def _shard_paths(path: Path) -> list[Path]:
    match = _SPLIT_NAME.search(path.name)
    if not match:
        return [path]
    prefix = path.name[:match.start()]
    total = int(match.group(2))
    expected = [
        path.with_name(f"{prefix}-{index:05d}-of-{total:05d}.gguf")
        for index in range(1, total + 1)
    ]
    return [shard for shard in expected if shard.is_file()]


def read_local(path) -> dict:
    """Return GGUF architecture fields and byte sizes for a file and its shards."""
    model_path = Path(path)
    reader_class = _bounded_reader(_estimator())
    shard_paths = _shard_paths(model_path)
    metadata = {}
    for shard in shard_paths:
        try:
            metadata.update(reader_class(str(shard)).read().metadata)
        except (struct.error, ValueError) as exc:
            raise ValueError(f"Malformed or truncated GGUF file {shard}: {exc}") from exc

    architecture = metadata.get("general.architecture")
    name = metadata.get("general.name", "")
    if not isinstance(architecture, (str, type(None))) or not isinstance(name, str):
        raise ValueError(f"Malformed GGUF file {model_path}: architecture and name must be strings")
    prefix = f"{architecture}." if architecture else None

    def field(suffix):
        return metadata.get(prefix + suffix) if prefix else None

    file_sizes = {str(shard): shard.stat().st_size for shard in shard_paths}
    n_layers = field("block_count")
    sliding_window = field("attention.sliding_window_size")
    # Match the estimator's known Scout fallback and ordinary sliding-window rules.
    if sliding_window:
        sliding_layers, full_layers = n_layers, 0
    elif "scout" in name.lower():
        sliding_layers, full_layers, sliding_window = 36, 12, 8192
    elif n_layers is not None:
        sliding_layers, full_layers = 0, n_layers
    else:
        sliding_layers = full_layers = None

    return {
        "architecture": architecture,
        "n_layers": n_layers,
        "n_head_kv": field("attention.head_count_kv"),
        "key_length": field("attention.key_length"),
        "value_length": field("attention.value_length"),
        "sliding_window_size": sliding_window,
        "sliding_window_layers": sliding_layers,
        "full_attention_layers": full_layers,
        "file_sizes_bytes": file_sizes,
        "total_size_bytes": sum(file_sizes.values()),
    }
