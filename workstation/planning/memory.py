"""KV cache size and the unified-memory plan (P1). Planned: #27.

Strix Halo memory is shared by CPU and GPU, so every part is counted once against one total.
"""

# Bytes per cached element, by llama.cpp cache type (q8_0: 34 bytes per 32; q4_0: 18 per 32).
CACHE_TYPE_BYTES = {"f16": 2.0, "bf16": 2.0, "q8_0": 1.0625, "q4_0": 0.5625}


def kv_cache_bytes(*, n_layers, n_head_kv, key_length, value_length, ctx,
                   cache_type="f16", swa_layers=0, swa_window=0) -> int:
    raise NotImplementedError("TODO #27")


def memory_plan(*, weights_bytes, kv_bytes, runtime_reserve_bytes, desktop_reserve_bytes,
                total_bytes) -> dict:
    raise NotImplementedError("TODO #27")
