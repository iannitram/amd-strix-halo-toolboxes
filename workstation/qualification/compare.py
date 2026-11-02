"""Compare a candidate's measurements with the current recipe's (R3). Planned: #26."""

# (metric, which direction is better)
METRICS = (
    ("load_seconds", "lower"),
    ("ttft_seconds", "lower"),
    ("prefill_tps", "higher"),
    ("decode_tps", "higher"),
)


def compare_to_baseline(baseline, candidate, thresholds) -> list:
    directions = dict(METRICS)
    unknown = next((metric for metric in thresholds if metric not in directions), None)
    if unknown is not None:
        raise ValueError(f"unknown metric: {unknown}")

    rows = []
    for metric, direction in METRICS:
        if metric not in thresholds:
            continue

        baseline_value = baseline.get(metric)
        candidate_value = candidate.get(metric)
        threshold_pct = thresholds[metric]
        if baseline_value is None or candidate_value is None or baseline_value == 0:
            change_pct = None
            status = "unknown"
        else:
            change_pct = round((candidate_value - baseline_value) / baseline_value * 100, 1)
            if direction == "lower":
                status = "failed" if change_pct > threshold_pct else "passed"
            else:
                status = "failed" if change_pct < -threshold_pct else "passed"

        rows.append({
            "metric": metric,
            "baseline": baseline_value,
            "candidate": candidate_value,
            "change_pct": change_pct,
            "threshold_pct": threshold_pct,
            "status": status,
        })

    return rows
