"""Tiny metadata-only GGUF fixtures for the local reader."""

import struct

import pytest

from workstation.planning.gguf_meta import read_local


def _string(value):
    encoded = value.encode("utf-8")
    return struct.pack("<Q", len(encoded)) + encoded


def _gguf(path, metadata):
    entries = []
    for key, value in metadata:
        entries.append(_string(key))
        if isinstance(value, str):
            entries.extend((struct.pack("<I", 8), _string(value)))
        else:
            entries.extend((struct.pack("<I", 4), struct.pack("<I", value)))
    path.write_bytes(struct.pack("<IIQQ", 0x46554747, 3, 0, len(metadata)) + b"".join(entries))


def test_read_local_returns_architecture_fields_and_missing_values(tmp_path):
    model = tmp_path / "model.gguf"
    _gguf(model, [
        ("general.architecture", "llama"),
        ("llama.block_count", 32),
        ("llama.attention.head_count_kv", 8),
        ("llama.attention.key_length", 128),
        ("llama.attention.value_length", 128),
    ])

    result = read_local(model)

    assert result["architecture"] == "llama"
    assert result["n_layers"] == 32
    assert result["n_head_kv"] == 8
    assert result["key_length"] == result["value_length"] == 128
    assert result["sliding_window_size"] is None
    assert result["file_sizes_bytes"] == {str(model): model.stat().st_size}
    assert result["total_size_bytes"] == model.stat().st_size


def test_read_local_combines_sizes_from_all_split_shards(tmp_path):
    metadata = [
        ("general.architecture", "mistral"),
        ("mistral.block_count", 40),
        ("mistral.attention.head_count_kv", 8),
        ("mistral.attention.key_length", 128),
        ("mistral.attention.value_length", 128),
        ("mistral.attention.sliding_window_size", 4096),
    ]
    first = tmp_path / "weights-00001-of-00002.gguf"
    second = tmp_path / "weights-00002-of-00002.gguf"
    _gguf(first, metadata)
    _gguf(second, metadata[:2])

    result = read_local(second)

    assert result["sliding_window_size"] == 4096
    assert result["sliding_window_layers"] == 40
    assert result["full_attention_layers"] == 0
    assert result["file_sizes_bytes"] == {
        str(first): first.stat().st_size,
        str(second): second.stat().st_size,
    }
    assert result["total_size_bytes"] == first.stat().st_size + second.stat().st_size


def test_truncated_and_oversized_files_raise_clean_errors(tmp_path):
    header = struct.pack("<IIQQ", 0x46554747, 3, 0, 1)
    empty = tmp_path / "empty.gguf"
    empty.write_bytes(b"")
    truncated = tmp_path / "truncated.gguf"
    truncated.write_bytes(header + struct.pack("<Q", 12) + b"general.arch")
    oversized = tmp_path / "oversized.gguf"
    oversized.write_bytes(header + struct.pack("<Q", 2**40) + b"general.architecture")

    with pytest.raises(ValueError, match="truncated"):
        read_local(empty)
    with pytest.raises(ValueError, match="truncated"):
        read_local(truncated)
    with pytest.raises(ValueError, match="past the end of the file"):
        read_local(oversized)
