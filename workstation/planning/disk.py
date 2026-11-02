"""Shard completeness and the disk plan (P1). Planned: #28."""

import math
import re


_SHARD_NAME = re.compile(r"^(?P<stem>.+)-(?P<index>[0-9]{5})-of-(?P<count>[0-9]{5})\.gguf$")


def check_shards(names) -> dict:
    groups = {}
    for name in names:
        match = _SHARD_NAME.fullmatch(name)
        if match is None:
            continue
        stem = match.group("stem")
        count = int(match.group("count"))
        if stem not in groups:
            groups[stem] = {"count": count, "names": set()}
        groups[stem]["count"] = max(groups[stem]["count"], count)
        groups[stem]["names"].add(name)

    missing = []
    stems = sorted(groups)
    for stem in stems:
        count = groups[stem]["count"]
        present = groups[stem]["names"]
        missing.extend(
            f"{stem}-{index:05d}-of-{count:05d}.gguf"
            for index in range(1, count + 1)
            if f"{stem}-{index:05d}-of-{count:05d}.gguf" not in present
        )
    return {"complete": not missing, "missing": sorted(missing), "groups": stems}


def plan_disk(files, *, temp_factor=0.0, cache_bytes=0, free_bytes=None) -> dict:
    download_bytes = 0
    reusable_bytes = 0
    for file in files:
        size = file["size"]
        if size < 0:
            raise ValueError("sizes must be >= 0")
        if file.get("present", False):
            reusable_bytes += size
        else:
            download_bytes += size

    if cache_bytes < 0 or temp_factor < 0:
        raise ValueError("sizes must be >= 0")
    temp_bytes = math.ceil(download_bytes * temp_factor)
    required_bytes = download_bytes + temp_bytes + cache_bytes
    if free_bytes is None:
        fits, status = None, "unknown"
    else:
        fits = required_bytes <= free_bytes
        status = "fits" if fits else "does-not-fit"
    return {
        "download_bytes": download_bytes,
        "reusable_bytes": reusable_bytes,
        "temp_bytes": temp_bytes,
        "cache_bytes": cache_bytes,
        "required_bytes": required_bytes,
        "free_bytes": free_bytes,
        "fits": fits,
        "status": status,
    }
