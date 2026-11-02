"""Explained resource plans and backend-declared alternatives (P1, #4).

This module only combines supplied facts; it never reads files, samples a clock or
contacts a backend. Numeric resource values and assumptions use ``label_value``.
"""

import math
from copy import deepcopy

from workstation.planning.disk import check_shards, plan_disk
from workstation.planning.labels import label_value
from workstation.planning.memory import CACHE_TYPE_BYTES, kv_cache_bytes, memory_plan


def _size(value, field, *, positive=False):
    if value is not None and (
        not isinstance(value, int) or isinstance(value, bool) or value < int(positive)
    ):
        bound = "positive" if positive else "non-negative"
        raise ValueError(f"{field} must be a {bound} integer")
    return value


def _status(fits):
    return "unknown" if fits is None else "fits" if fits else "does-not-fit"


def _combined_fit(*values):
    if False in values:
        return False
    return None if None in values else True


def _files(model_meta):
    if "files" in model_meta:
        # A pre-download manifest uses the same shape as disk.plan_disk.
        return [dict(file) for file in model_meta["files"]]
    sizes = model_meta.get("file_sizes_bytes")
    if sizes is None:
        return []
    return [{"name": name, "size": size, "present": True} for name, size in sizes.items()]


def plan(model_meta, choices, host) -> dict:
    """Combine GGUF metadata, user choices and a host snapshot into a pure plan.

    ``model_meta`` accepts ``gguf_meta.read_local`` output, or a remote manifest
    with ``files=[{name, size, present?}]`` (size may be None). A complete manifest
    can supply weights by summing sizes when ``total_size_bytes`` is unavailable.
    Shards missing from the manifest invalidate weights and download totals.

    Choices: ``ctx_size`` is context *per user*, ``parallel`` is the user count,
    ``cache_type`` applies to both K and V. Runtime/desktop reserves in bytes must
    be explicit. ``temp_factor`` and disk ``cache_bytes`` default to zero (no
    extra preparation copy or disk cache). Missing other inputs remain unknown.

    Host memory uses ``memory.total_bytes`` once, with ``disk_free_bytes`` for
    storage. Host measurements are aged using ``host.sampled_at`` and optional
    ``choices.now``/``stale_after_s``; without both times they are labelled stale.
    ``model_meta.observed_at`` similarly dates reusable local file sizes.
    """
    uncertainties = []

    def labelled(value, field, *, measured=False, observed_at=None):
        result = label_value(
            value, source="measured" if measured else "estimate",
            observed_at=observed_at, now=choices.get("now"),
            stale_after_s=choices.get("stale_after_s", 300),
        )
        if result["label"] in ("unknown", "stale"):
            uncertainties.append(f"{field}: {result['label']}")
        return result

    ctx = _size(choices.get("ctx_size"), "ctx_size", positive=True)
    parallel = _size(choices.get("parallel"), "parallel", positive=True)
    cache_type = choices.get("cache_type")
    if cache_type is not None and cache_type not in CACHE_TYPE_BYTES:
        raise ValueError(f"unknown cache type: {cache_type}")

    files = _files(model_meta)
    shards = check_shards(file["name"] for file in files)
    if not files:
        shards["complete"] = None
        uncertainties.append("Model file manifest is unknown")
    elif not shards["complete"]:
        uncertainties.append("Missing model shards: " + ", ".join(shards["missing"]))
    for file in files:
        _size(file.get("size"), "file size")

    weights = _size(model_meta.get("total_size_bytes"), "total_size_bytes")
    if weights is None and files and all(file.get("size") is not None for file in files):
        weights = sum(file["size"] for file in files)
    if shards["complete"] is False:
        weights = None

    fields = ("n_layers", "n_head_kv", "key_length", "value_length", "sliding_window_layers")
    dimensions = {key: _size(model_meta.get(key), key) for key in fields}
    window = _size(model_meta.get("sliding_window_size"), "sliding_window_size")
    missing = [key for key, value in dimensions.items() if value is None]
    if not model_meta.get("architecture"):
        missing.append("architecture")
    if dimensions["sliding_window_layers"] and not window:
        missing.append("sliding_window_size")
    if missing:
        uncertainties.append("Missing KV metadata: " + ", ".join(missing))
    kv = None
    if not missing and ctx is not None and parallel is not None and cache_type is not None:
        kv = kv_cache_bytes(
            n_layers=dimensions["n_layers"], n_head_kv=dimensions["n_head_kv"],
            key_length=dimensions["key_length"], value_length=dimensions["value_length"],
            ctx=ctx, cache_type=cache_type, swa_layers=dimensions["sliding_window_layers"],
            swa_window=window or 0,
        ) * parallel
    if cache_type is None:
        uncertainties.append("cache_type: unknown")

    runtime = _size(choices.get("runtime_reserve_bytes"), "runtime_reserve_bytes")
    desktop = _size(choices.get("desktop_reserve_bytes"), "desktop_reserve_bytes")
    total = _size(host.get("memory", {}).get("total_bytes"), "memory.total_bytes")
    parts = dict(weights=weights, kv_cache=kv, runtime_reserve=runtime, desktop_reserve=desktop)
    if all(value is not None for value in parts.values()):
        memory = memory_plan(
            weights_bytes=weights, kv_bytes=kv, runtime_reserve_bytes=runtime,
            desktop_reserve_bytes=desktop, total_bytes=total,
        )
    else:
        memory = dict(parts=parts, required=None, total=total, headroom=None,
                      fits=None, status="unknown")
    memory["parts"] = {
        key: labelled(value, f"memory.parts.{key}") for key, value in parts.items()
    }
    for key in ("required", "total", "headroom"):
        memory[key] = labelled(memory[key], f"memory.{key}", measured=key == "total",
                               observed_at=host.get("sampled_at"))

    temp_factor = choices.get("temp_factor", 0.0)
    if (not isinstance(temp_factor, (int, float)) or isinstance(temp_factor, bool)
            or not math.isfinite(temp_factor) or temp_factor < 0):
        raise ValueError("temp_factor must be finite and non-negative")
    cache = _size(choices.get("cache_bytes", 0), "cache_bytes")
    free = _size(host.get("disk_free_bytes"), "disk_free_bytes")
    # The primitive accepts only known sizes; invalidate affected aggregates below.
    disk = plan_disk(
        [{**file, "size": file.get("size") or 0} for file in files],
        temp_factor=temp_factor, cache_bytes=cache or 0, free_bytes=free,
    )
    download_unknown = not shards["complete"] or any(
        file.get("size") is None and not file.get("present", False) for file in files
    )
    reuse_unknown = not files or any(
        file.get("size") is None and file.get("present", False) for file in files
    )
    if download_unknown:
        disk.update(download_bytes=None, temp_bytes=None)
    if reuse_unknown:
        disk["reusable_bytes"] = None
    disk["cache_bytes"] = cache
    if download_unknown or cache is None:
        disk.update(required_bytes=None, fits=None, status="unknown")
    for key, value in disk.copy().items():
        if key in ("fits", "status"):
            continue
        measured = key in ("free_bytes", "reusable_bytes")
        observed = host.get("sampled_at") if key == "free_bytes" else model_meta.get("observed_at")
        disk[key] = labelled(value, f"disk.{key}", measured=measured, observed_at=observed)

    uncertainties.append("Memory allocations and reserves are estimates; GPU use is unverified")
    sizes_known = True if files and all(file.get("size") is not None for file in files) else None
    fits = _combined_fit(memory["fits"], disk["fits"], shards["complete"], sizes_known)
    return {
        "memory": memory, "disk": disk, "shards": shards,
        "assumptions": {
            "ctx_size": labelled(ctx, "ctx_size"), "parallel": labelled(parallel, "parallel"),
            "cache_type": cache_type, "temp_factor": labelled(temp_factor, "temp_factor"),
        },
        "fits": fits, "status": _status(fits), "uncertainties": uncertainties,
    }


def alternatives(model_meta, choices, host, *, backend) -> list:
    """Try one smaller setting at a time, only in explicitly supported combinations.

    ``backend`` is ``{supported_choices: [{ctx_size, cache_type, parallel}, ...]}``.
    Each entry declares a complete supported combination, not independent option
    lists whose cross-product might be invalid. Absent capabilities allow nothing.
    Returns ``[{changes: {setting: value}, plan: <plan result>}, ...]`` in context,
    cache, user order (largest reductions last). Unknown cache types are omitted.
    """
    supported = backend.get("supported_choices", [])
    result = []
    keys = ("ctx_size", "cache_type", "parallel")
    current = {key: choices.get(key) for key in keys}
    for key in keys:
        candidates = set()
        for entry in supported:
            if (any(key not in entry for key in keys)
                    or entry["cache_type"] not in CACHE_TYPE_BYTES
                    or any(not isinstance(entry[key], int) or isinstance(entry[key], bool)
                           or entry[key] <= 0 for key in ("ctx_size", "parallel"))):
                continue
            if any(entry.get(other) != current[other] for other in keys if other != key):
                continue
            value = entry.get(key)
            if key == "cache_type":
                smaller = (value in CACHE_TYPE_BYTES and current[key] in CACHE_TYPE_BYTES
                           and CACHE_TYPE_BYTES[value] < CACHE_TYPE_BYTES[current[key]])
            else:
                smaller = (isinstance(value, int) and not isinstance(value, bool) and value > 0
                           and current[key] is not None and value < current[key])
            if smaller:
                candidates.add(value)
        order = (lambda value: (CACHE_TYPE_BYTES[value], value)) if key == "cache_type" else None
        for value in sorted(candidates, key=order, reverse=True):
            candidate = deepcopy(choices)
            candidate[key] = value
            result.append({"changes": {key: value}, "plan": plan(model_meta, candidate, host)})
    return result
