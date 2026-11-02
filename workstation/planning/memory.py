"""KV cache size and the unified-memory plan (P1). Planned: #27.

Strix Halo memory is shared by CPU and GPU, so every part is counted once against one total.
"""

# Bytes per cached element, by llama.cpp cache type (q8_0: 34 bytes per 32; q4_0: 18 per 32).
CACHE_TYPE_BYTES = {"f16": 2.0, "bf16": 2.0, "q8_0": 1.0625, "q4_0": 0.5625}


def kv_cache_bytes(*, n_layers, n_head_kv, key_length, value_length, ctx,
                   cache_type="f16", swa_layers=0, swa_window=0) -> int:
    if cache_type not in CACHE_TYPE_BYTES:
        raise ValueError(f"unknown cache type: {cache_type}")

    sizes = (n_layers, n_head_kv, key_length, value_length, ctx, swa_layers, swa_window)
    if any(size < 0 for size in sizes):
        raise ValueError("sizes must be >= 0")
    if swa_layers > n_layers:
        raise ValueError("swa_layers must be <= n_layers")

    full_attention_layers = n_layers - swa_layers
    sliding_window_tokens = min(ctx, swa_window)
    elements = n_head_kv * (key_length + value_length)
    cached_elements = elements * (
        full_attention_layers * ctx + swa_layers * sliding_window_tokens
    )
    return int(-(-cached_elements * CACHE_TYPE_BYTES[cache_type] // 1))


def memory_plan(*, weights_bytes, kv_bytes, runtime_reserve_bytes, desktop_reserve_bytes,
                total_bytes) -> dict:
    parts = {
        "weights": weights_bytes,
        "kv_cache": kv_bytes,
        "runtime_reserve": runtime_reserve_bytes,
        "desktop_reserve": desktop_reserve_bytes,
    }
    sizes = tuple(parts.values()) + (() if total_bytes is None else (total_bytes,))
    if any(size < 0 for size in sizes):
        raise ValueError("sizes must be >= 0")

    required = sum(parts.values())
    if total_bytes is None:
        total = headroom = fits = None
        status = "unknown"
    else:
        total = total_bytes
        headroom = total - required
        fits = required <= total
        status = "fits" if fits else "does-not-fit"

    return {
        "parts": parts,
        "required": required,
        "total": total,
        "headroom": headroom,
        "fits": fits,
        "status": status,
    }
