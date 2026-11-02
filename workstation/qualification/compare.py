"""Compare a candidate's measurements with the current recipe's (R3). Planned: #26."""

# (metric, which direction is better)
METRICS = (
    ("load_seconds", "lower"),
    ("ttft_seconds", "lower"),
    ("prefill_tps", "higher"),
    ("decode_tps", "higher"),
)


def compare_to_baseline(baseline, candidate, thresholds) -> list:
    raise NotImplementedError("TODO #26")
