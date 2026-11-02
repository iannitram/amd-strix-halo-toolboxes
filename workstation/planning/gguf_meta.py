"""Structured GGUF metadata from local files, reusing the existing estimator."""

import importlib.util
import os
import re
import struct
from pathlib import Path


_ESTIMATOR_PATH = Path(__file__).resolve().parents[2] / "toolboxes" / "gguf-vram-estimator.py"
# Byte sizes of the fixed-width GGUF value types (u8 i8 u16 i16 u32 i32 f32 bool u64 i64 f64).
_FIXED_SIZES = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
_MAX_ARRAY_DEPTH = 32
_SPLIT_NAME = re.compile(r"-(\d{5})-of-(\d{5})\.gguf$", re.IGNORECASE)


def _estimator():
    spec = importlib.util.spec_from_file_location("gguf_vram_estimator", _ESTIMATOR_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load GGUF estimator at {_ESTIMATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bounded_reader(estimator):
    """The estimator's reader, except every string, skip and array is bounded by the file size.

    Without these checks a malformed length header asks for a huge allocation, or a skip runs
    past the end of the file, before any read fails.
    """

    class BoundedReader(estimator.GGUFMetadataReader):
        def _read_string(self) -> str:
            header = self.f.read(8)
            if len(header) != 8:
                raise ValueError("truncated GGUF string header")
            (length,) = struct.unpack("<Q", header)
            if length > self._remaining():
                raise ValueError("GGUF string runs past the end of the file")
            return self.f.read(length).decode("utf-8", errors="replace")

        def _remaining(self) -> int:
            return os.fstat(self.f.fileno()).st_size - self.f.tell()

        def _skip_bytes(self, size: int):
            if size > self._remaining():
                raise ValueError("GGUF value runs past the end of the file")
            self.f.seek(size, 1)

        def _skip_value(self, value_type_idx: int, depth: int = 0):
            # The estimator ignores 64-bit types, skips nested arrays as strings and seeks
            # past the end of the file; every skip here is checked against the file size.
            if value_type_idx in _FIXED_SIZES:
                self._skip_bytes(_FIXED_SIZES[value_type_idx])
            elif value_type_idx == 8:
                header = self.f.read(8)
                if len(header) != 8:
                    raise ValueError("truncated GGUF string header")
                self._skip_bytes(struct.unpack("<Q", header)[0])
            elif value_type_idx == 9:
                header = self.f.read(12)
                if len(header) != 12:
                    raise ValueError("truncated GGUF array header")
                item_type, count = struct.unpack("<IQ", header)
                if item_type in _FIXED_SIZES:
                    self._skip_bytes(count * _FIXED_SIZES[item_type])
                elif item_type in (8, 9):
                    if depth >= _MAX_ARRAY_DEPTH:
                        raise ValueError("GGUF arrays nested too deeply")
                    # Each string or array item takes at least 8 bytes of header.
                    if count * 8 > self._remaining():
                        raise ValueError("GGUF array runs past the end of the file")
                    for _ in range(count):
                        self._skip_value(item_type, depth + 1)
                else:
                    raise ValueError(f"unknown GGUF array item type {item_type}")
            else:
                raise ValueError(f"unknown GGUF value type {value_type_idx}")

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

    file_sizes = {str(shard): shard.stat().st_size for shard in shard_paths}
    return _metadata_result(metadata, file_sizes)


def _metadata_result(metadata: dict, file_sizes: dict[str, int]) -> dict:
    """Keep the local and remote planners' metadata fields identical."""
    architecture = metadata.get("general.architecture")
    name = metadata.get("general.name", "")
    if not isinstance(architecture, (str, type(None))) or not isinstance(name, str):
        raise ValueError("Malformed GGUF metadata: architecture and name must be strings")
    prefix = f"{architecture}." if architecture else None

    def field(suffix):
        return metadata.get(prefix + suffix) if prefix else None

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
