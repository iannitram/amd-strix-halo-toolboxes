"""Shard completeness and the disk plan (P1). Planned: #28."""


def check_shards(names) -> dict:
    raise NotImplementedError("TODO #28")


def plan_disk(files, *, temp_factor=0.0, cache_bytes=0, free_bytes=None) -> dict:
    raise NotImplementedError("TODO #28")
